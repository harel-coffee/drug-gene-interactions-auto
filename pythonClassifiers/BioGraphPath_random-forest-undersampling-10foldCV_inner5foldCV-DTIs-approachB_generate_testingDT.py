import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn import metrics
from collections import Counter
from imblearn.under_sampling import RandomUnderSampler
from imblearn.under_sampling import NearMiss 
from numpy import mean
from numpy import std
from numpy import argmax
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_selection import SelectFromModel

from sklearn.tree import export_graphviz
   #from sklearn.externals.six import StringIO
from six import StringIO
from IPython.display import Image
import pydotplus
import collections

#save decision tree in a png file
def saveTree(dt, features, d):
   dot_data = StringIO()
   export_graphviz(dt, out_file=dot_data,  
                filled=True, rounded=True, impurity=False,
                special_characters=True,feature_names = features,class_names=['NO-INTERACT','INTERACT'])
   graph = pydotplus.graph_from_dot_data(dot_data.getvalue())

   #fucking colors...
##   colors = ('lightcoral', 'springgreen', 'white')
##   nodes = graph.get_node_list()
##   for node in nodes:
##      if node.get_name() not in ('node', 'edge'):
##         values = dt.tree_.value[int(node.get_name())][0]
##        #color only LEAF nodes with one class winning
##         if max(values) > sum(values)/2:    
##            node.set_fillcolor(colors[np.argmax(values)])
##        #nodes with same values for both classes get the default color
##         else:
##            node.set_fillcolor(colors[-1])
   #end of addition
            
   graph.write_png('decisiontree_approx_'+str(d)+'.png')
   Image(graph.create_png())
   print('extracted DT in a png file...')
   
# This function runs the outer 10-fold CV
def tenFoldCV(X, y, cv, model, header):
   precision = np.zeros(10)
   recall = np.zeros(10)
   f1=np.zeros(10)
   testdt_X = pd.DataFrame()
   testdt_y = pd.DataFrame()
   
   i=0
   for train_index, test_index in cv.split(X, y):
         print("Run ", i+1)
         #print("TRAIN:", train_index, "TEST:", test_index)
         X_train, X_test = X[train_index], X[test_index] 
         y_train, y_test = y.iloc[train_index], y.iloc[test_index]

         print("Calling inner 5-fold CV to decide undersampling strategy for this fold")
         strategy = runInnerCV(X_train, y_train)
         algo = strategy[0]
         ratio= strategy[1]

         if strategy[0]==0:
            undersample2 = RandomUnderSampler(sampling_strategy=ratio)
         else: 
            undersample2 = NearMiss(version=1, n_neighbors=3, sampling_strategy=ratio)
         X_train, y_train = undersample2.fit_resample(X_train, y_train)
         print('Inner 5-fold CV decided undersampling training ratio: ',ratio)

         print("model fit...")
         model.fit(X_train, y_train)
         print("prediction")
         y_pred = model.predict(X_test)
         dt_X = pd.DataFrame(X_test, columns = header[0])
         testdt_X= pd.concat([testdt_X,dt_X])
         dt_y = pd.DataFrame(y_pred, columns = ['Prediction'])
         testdt_y= pd.concat([testdt_y,dt_y])
         precision[i]=metrics.precision_score(y_test, y_pred)
         recall[i]=metrics.recall_score(y_test, y_pred)
         f1[i]=metrics.f1_score(y_test, y_pred)
         print("f1[i]=",f1[i])
         i=i+1
   r = dict()
   r['Precision'] = mean(precision)
   r['Recall']   = mean(recall)
   r['f1score'] = mean(f1)
   return r, testdt_X, testdt_y

# This function runs the outer 10-fold CV
def runInnerCV(inner_X, inner_y):

   strategyList = [0,0]
   strategy = 0
   maxf1=0
   #ratios=[0.03, 0.04, 0.05, 0.055, 0.06, 0.075]
   ratios=[0.2]#[0.11, 0.15, 0.17, 0.2, 0.25]
   inner_cv = StratifiedKFold(n_splits=5, random_state=1, shuffle=True)
      
   while strategy<2:
      for ratio in ratios:
         f1=np.zeros(5)
         i=0
         model2=RandomForestClassifier(n_estimators=100)
         for inner_train_index, inner_test_index in inner_cv.split(inner_X, inner_y):
               inner_X_train, inner_X_test = inner_X[inner_train_index], inner_X[inner_test_index] 
               inner_y_train, inner_y_test = inner_y.iloc[inner_train_index], inner_y.iloc[inner_test_index]
               if strategy==0:
                  inner_undersample = RandomUnderSampler(sampling_strategy=ratio)
               else: 
                  inner_undersample = NearMiss(version=1, n_neighbors=3, sampling_strategy=ratio)
               X_under, y_under = inner_undersample.fit_resample(inner_X_train, inner_y_train)
               model2.fit(X_under, y_under)
               inner_y_pred = model2.predict(inner_X_test)
               f1[i]=metrics.f1_score(inner_y_test, inner_y_pred)
               i=i+1
         f1_score = mean(f1)
         #check if this undersampling strategy (algo and ratio) reached the best f1 score
         if f1_score> maxf1:
            maxf1=f1_score
            strategyList[0]=strategy
            strategyList[1]=ratio
      strategy= strategy+1
   #return the strategy with the best score   
   return strategyList

def main():
   data = pd.read_csv("DTI-enriched_sematyp_featuresExtended_corrected.csv")
   #data = pd.read_csv("DTI-enriched_sematyp_featuresExtended_NoLITER_DTI.csv")
   #data = pd.read_csv("/media/fot/USB-FOT/FOT/Research/Graph analysis @dimokritos/Drug target interactions/FeatureExtraction/DTI-enriched_sematyp_features.csv")

   #train model

   feature_cols=["nod1_aapp", "nod1_acab", "nod1_acty", "nod1_aggp", "nod1_amas", "nod1_amph", "nod1_anab", "nod1_anim", "nod1_anst", "nod1_antb", "nod1_arch", "nod1_bacs", "nod1_bact", "nod1_bdsu", "nod1_bdsy", "nod1_bhvr", "nod1_biof", "nod1_bird", "nod1_blor", "nod1_bmod", "nod1_bodm", "nod1_bpoc", "nod1_bsoj", "nod1_celc", "nod1_celf", "nod1_cell", "nod1_cgab", "nod1_chem", "nod1_chvf", "nod1_chvs", "nod1_clas", "nod1_clna", "nod1_clnd", "nod1_cnce", "nod1_comd", "nod1_crbs", "nod1_diap", "nod1_dora", "nod1_drdd", "nod1_dsyn", "nod1_edac", "nod1_eehu", "nod1_elii", "nod1_emod", "nod1_emst", "nod1_enty", "nod1_enzy", "nod1_euka", "nod1_evnt", "nod1_famg", "nod1_ffas", "nod1_fish", "nod1_fndg", "nod1_fngs", "nod1_food", "nod1_ftcn", "nod1_genf", "nod1_geoa", "nod1_gngm", "nod1_gora", "nod1_grpa", "nod1_grup", "nod1_hcpp", "nod1_hcro", "nod1_hlca", "nod1_hops", "nod1_horm", "nod1_humn", "nod1_idcn", "nod1_imft", "nod1_inbe", "nod1_inch", "nod1_inpo", "nod1_inpr", "nod1_irda", "nod1_lang", "nod1_lbpr", "nod1_lbtr", "nod1_mamm", "nod1_mbrt", "nod1_mcha", "nod1_medd", "nod1_menp", "nod1_mnob", "nod1_mobd", "nod1_moft", "nod1_mosq", "nod1_neop", "nod1_nnon", "nod1_npop", "nod1_nusq", "nod1_ocac", "nod1_ocdi", "nod1_orch", "nod1_orga", "nod1_orgf", "nod1_orgm", "nod1_orgt", "nod1_ortf", "nod1_patf", "nod1_phob", "nod1_phpr", "nod1_phsf", "nod1_phsu", "nod1_plnt", "nod1_podg", "nod1_popg", "nod1_prog", "nod1_pros", "nod1_qlco", "nod1_qnco", "nod1_rcpt", "nod1_rept", "nod1_resa", "nod1_resd", "nod1_rnlw", "nod1_sbst", "nod1_shro", "nod1_socb", "nod1_sosy", "nod1_spco", "nod1_tisu", "nod1_tmco", "nod1_topp", "nod1_virs", "nod1_vita", "nod1_vtbt", "rel1_ADMINISTERED_TO", "rel1_AFFECTS", "rel1_ASSOCIATED_WITH", "rel1_AUGMENTS", "rel1_CAUSES", "rel1_COEXISTS_WITH", "rel1_compared_with", "rel1_COMPLICATES", "rel1_CONVERTS_TO", "rel1_DIAGNOSES", "rel1_different_from", "rel1_different_than", "rel1_DISRUPTS", "rel1_higher_than", "rel1_INHIBITS", "rel1_INTERACTS_WITH", "rel1_IS_A", "rel1_ISA", "rel1_LOCATION_OF", "rel1_lower_than", "rel1_MANIFESTATION_OF", "rel1_METHOD_OF", "rel1_OCCURS_IN", "rel1_PART_OF", "rel1_PRECEDES", "rel1_PREDISPOSES", "rel1_PREVENTS", "rel1_PROCESS_OF", "rel1_PRODUCES", "rel1_same_as", "rel1_STIMULATES", "rel1_TREATS", "rel1_USES", "rel1_MENTIONED_IN", "rel1_HAS_MESH", "rel1_LITERATURE_DTI", "nod2_aapp", "nod2_acab", "nod2_acty", "nod2_aggp", "nod2_amas", "nod2_amph", "nod2_anab", "nod2_anim", "nod2_anst", "nod2_antb", "nod2_arch", "nod2_bacs", "nod2_bact", "nod2_bdsu", "nod2_bdsy", "nod2_bhvr", "nod2_biof", "nod2_bird", "nod2_blor", "nod2_bmod", "nod2_bodm", "nod2_bpoc", "nod2_bsoj", "nod2_celc", "nod2_celf", "nod2_cell", "nod2_cgab", "nod2_chem", "nod2_chvf", "nod2_chvs", "nod2_clas", "nod2_clna", "nod2_clnd", "nod2_cnce", "nod2_comd", "nod2_crbs", "nod2_diap", "nod2_dora", "nod2_drdd", "nod2_dsyn", "nod2_edac", "nod2_eehu", "nod2_elii", "nod2_emod", "nod2_emst", "nod2_enty", "nod2_enzy", "nod2_euka", "nod2_evnt", "nod2_famg", "nod2_ffas", "nod2_fish", "nod2_fndg", "nod2_fngs", "nod2_food", "nod2_ftcn", "nod2_genf", "nod2_geoa", "nod2_gngm", "nod2_gora", "nod2_grpa", "nod2_grup", "nod2_hcpp", "nod2_hcro", "nod2_hlca", "nod2_hops", "nod2_horm", "nod2_humn", "nod2_idcn", "nod2_imft", "nod2_inbe", "nod2_inch", "nod2_inpo", "nod2_inpr", "nod2_irda", "nod2_lang", "nod2_lbpr", "nod2_lbtr", "nod2_mamm", "nod2_mbrt", "nod2_mcha", "nod2_medd", "nod2_menp", "nod2_mnob", "nod2_mobd", "nod2_moft", "nod2_mosq", "nod2_neop", "nod2_nnon", "nod2_npop", "nod2_nusq", "nod2_ocac", "nod2_ocdi", "nod2_orch", "nod2_orga", "nod2_orgf", "nod2_orgm", "nod2_orgt", "nod2_ortf", "nod2_patf", "nod2_phob", "nod2_phpr", "nod2_phsf", "nod2_phsu", "nod2_plnt", "nod2_podg", "nod2_popg", "nod2_prog", "nod2_pros", "nod2_qlco", "nod2_qnco", "nod2_rcpt", "nod2_rept", "nod2_resa", "nod2_resd", "nod2_rnlw", "nod2_sbst", "nod2_shro", "nod2_socb", "nod2_sosy", "nod2_spco", "nod2_tisu", "nod2_tmco", "nod2_topp", "nod2_virs", "nod2_vita", "nod2_vtbt", "rel2_ADMINISTERED_TO", "rel2_AFFECTS", "rel2_ASSOCIATED_WITH", "rel2_AUGMENTS", "rel2_CAUSES", "rel2_COEXISTS_WITH", "rel2_compared_with", "rel2_COMPLICATES", "rel2_CONVERTS_TO", "rel2_DIAGNOSES", "rel2_different_from", "rel2_different_than", "rel2_DISRUPTS", "rel2_higher_than", "rel2_INHIBITS", "rel2_INTERACTS_WITH", "rel2_IS_A", "rel2_ISA", "rel2_LOCATION_OF", "rel2_lower_than", "rel2_MANIFESTATION_OF", "rel2_METHOD_OF", "rel2_OCCURS_IN", "rel2_PART_OF", "rel2_PRECEDES", "rel2_PREDISPOSES", "rel2_PREVENTS", "rel2_PROCESS_OF", "rel2_PRODUCES", "rel2_same_as", "rel2_STIMULATES", "rel2_TREATS", "rel2_USES", "rel2_MENTIONED_IN", "rel2_HAS_MESH", "rel2_LITERATURE_DTI", "nod3_aapp", "nod3_acab", "nod3_acty", "nod3_aggp", "nod3_amas", "nod3_amph", "nod3_anab", "nod3_anim", "nod3_anst", "nod3_antb", "nod3_arch", "nod3_bacs", "nod3_bact", "nod3_bdsu", "nod3_bdsy", "nod3_bhvr", "nod3_biof", "nod3_bird", "nod3_blor", "nod3_bmod", "nod3_bodm", "nod3_bpoc", "nod3_bsoj", "nod3_celc", "nod3_celf", "nod3_cell", "nod3_cgab", "nod3_chem", "nod3_chvf", "nod3_chvs", "nod3_clas", "nod3_clna", "nod3_clnd", "nod3_cnce", "nod3_comd", "nod3_crbs", "nod3_diap", "nod3_dora", "nod3_drdd", "nod3_dsyn", "nod3_edac", "nod3_eehu", "nod3_elii", "nod3_emod", "nod3_emst", "nod3_enty", "nod3_enzy", "nod3_euka", "nod3_evnt", "nod3_famg", "nod3_ffas", "nod3_fish", "nod3_fndg", "nod3_fngs", "nod3_food", "nod3_ftcn", "nod3_genf", "nod3_geoa", "nod3_gngm", "nod3_gora", "nod3_grpa", "nod3_grup", "nod3_hcpp", "nod3_hcro", "nod3_hlca", "nod3_hops", "nod3_horm", "nod3_humn", "nod3_idcn", "nod3_imft", "nod3_inbe", "nod3_inch", "nod3_inpo", "nod3_inpr", "nod3_irda", "nod3_lang", "nod3_lbpr", "nod3_lbtr", "nod3_mamm", "nod3_mbrt", "nod3_mcha", "nod3_medd", "nod3_menp", "nod3_mnob", "nod3_mobd", "nod3_moft", "nod3_mosq", "nod3_neop", "nod3_nnon", "nod3_npop", "nod3_nusq", "nod3_ocac", "nod3_ocdi", "nod3_orch", "nod3_orga", "nod3_orgf", "nod3_orgm", "nod3_orgt", "nod3_ortf", "nod3_patf", "nod3_phob", "nod3_phpr", "nod3_phsf", "nod3_phsu", "nod3_plnt", "nod3_podg", "nod3_popg", "nod3_prog", "nod3_pros", "nod3_qlco", "nod3_qnco", "nod3_rcpt", "nod3_rept", "nod3_resa", "nod3_resd", "nod3_rnlw", "nod3_sbst", "nod3_shro", "nod3_socb", "nod3_sosy", "nod3_spco", "nod3_tisu", "nod3_tmco", "nod3_topp", "nod3_virs", "nod3_vita", "nod3_vtbt", "rel3_ADMINISTERED_TO", "rel3_AFFECTS", "rel3_ASSOCIATED_WITH", "rel3_AUGMENTS", "rel3_CAUSES", "rel3_COEXISTS_WITH", "rel3_compared_with", "rel3_COMPLICATES", "rel3_CONVERTS_TO", "rel3_DIAGNOSES", "rel3_different_from", "rel3_different_than", "rel3_DISRUPTS", "rel3_higher_than", "rel3_INHIBITS", "rel3_INTERACTS_WITH", "rel3_IS_A", "rel3_ISA", "rel3_LOCATION_OF", "rel3_lower_than", "rel3_MANIFESTATION_OF", "rel3_METHOD_OF", "rel3_OCCURS_IN", "rel3_PART_OF", "rel3_PRECEDES", "rel3_PREDISPOSES", "rel3_PREVENTS", "rel3_PROCESS_OF", "rel3_PRODUCES", "rel3_same_as", "rel3_STIMULATES", "rel3_TREATS", "rel3_USES", "rel3_MENTIONED_IN", "rel3_HAS_MESH", "rel3_LITERATURE_DTI", "PATH0", "PATH1", "PATH2", "PATH3", "PATH4", "PATH5", "PATH6", "PATH7", "PATH8", "PATH9", "PATH10", "PATH11", "PATH12", "PATH13", "PATH14", "PATH15", "PATH16", "PATH17", "PATH18", "PATH19", "PATH20", "PATH21", "PATH22", "PATH23", "PATH24", "PATH25", "PATH26", "PATH27", "PATH28", "PATH29", "PATH30", "PATH31", "PATH32", "PATH33", "PATH34", "PATH35", "PATH36", "PATH37", "PATH38", "PATH39", "PATH40", "PATH41", "PATH42", "PATH43", "PATH44", "PATH45", "PATH46", "PATH47", "PATH48", "PATH49", "PATH50", "PATH51", "PATH52", "PATH53", "PATH54", "PATH55", "PATH56", "PATH57", "PATH58", "PATH59", "PATH60", "PATH61", "PATH62", "PATH63", "PATH64", "PATH65", "PATH66", "PATH67", "PATH68", "PATH69", "PATH70", "PATH71", "PATH72", "PATH73", "PATH74", "PATH75", "PATH76", "PATH77", "PATH78", "PATH79", "PATH80", "PATH81", "PATH82", "PATH83", "PATH84", "PATH85", "PATH86", "PATH87", "PATH88", "PATH89", "PATH90", "PATH91", "PATH92", "PATH93", "PATH94", "PATH95", "PATH96", "PATH97", "PATH98", "PATH99"]
   #feature_cols=["nod1_aapp", "nod1_acab", "nod1_acty", "nod1_aggp", "nod1_amas", "nod1_amph", "nod1_anab", "nod1_anim", "nod1_anst", "nod1_antb", "nod1_arch", "nod1_bacs", "nod1_bact", "nod1_bdsu", "nod1_bdsy", "nod1_bhvr", "nod1_biof", "nod1_bird", "nod1_blor", "nod1_bmod", "nod1_bodm", "nod1_bpoc", "nod1_bsoj", "nod1_celc", "nod1_celf", "nod1_cell", "nod1_cgab", "nod1_chem", "nod1_chvf", "nod1_chvs", "nod1_clas", "nod1_clna", "nod1_clnd", "nod1_cnce", "nod1_comd", "nod1_crbs", "nod1_diap", "nod1_dora", "nod1_drdd", "nod1_dsyn", "nod1_edac", "nod1_eehu", "nod1_elii", "nod1_emod", "nod1_emst", "nod1_enty", "nod1_enzy", "nod1_euka", "nod1_evnt", "nod1_famg", "nod1_ffas", "nod1_fish", "nod1_fndg", "nod1_fngs", "nod1_food", "nod1_ftcn", "nod1_genf", "nod1_geoa", "nod1_gngm", "nod1_gora", "nod1_grpa", "nod1_grup", "nod1_hcpp", "nod1_hcro", "nod1_hlca", "nod1_hops", "nod1_horm", "nod1_humn", "nod1_idcn", "nod1_imft", "nod1_inbe", "nod1_inch", "nod1_inpo", "nod1_inpr", "nod1_irda", "nod1_lang", "nod1_lbpr", "nod1_lbtr", "nod1_mamm", "nod1_mbrt", "nod1_mcha", "nod1_medd", "nod1_menp", "nod1_mnob", "nod1_mobd", "nod1_moft", "nod1_mosq", "nod1_neop", "nod1_nnon", "nod1_npop", "nod1_nusq", "nod1_ocac", "nod1_ocdi", "nod1_orch", "nod1_orga", "nod1_orgf", "nod1_orgm", "nod1_orgt", "nod1_ortf", "nod1_patf", "nod1_phob", "nod1_phpr", "nod1_phsf", "nod1_phsu", "nod1_plnt", "nod1_podg", "nod1_popg", "nod1_prog", "nod1_pros", "nod1_qlco", "nod1_qnco", "nod1_rcpt", "nod1_rept", "nod1_resa", "nod1_resd", "nod1_rnlw", "nod1_sbst", "nod1_shro", "nod1_socb", "nod1_sosy", "nod1_spco", "nod1_tisu", "nod1_tmco", "nod1_topp", "nod1_virs", "nod1_vita", "nod1_vtbt", "rel1_ADMINISTERED_TO", "rel1_AFFECTS", "rel1_ASSOCIATED_WITH", "rel1_AUGMENTS", "rel1_CAUSES", "rel1_COEXISTS_WITH", "rel1_compared_with", "rel1_COMPLICATES", "rel1_CONVERTS_TO", "rel1_DIAGNOSES", "rel1_different_from", "rel1_different_than", "rel1_DISRUPTS", "rel1_higher_than", "rel1_INHIBITS", "rel1_INTERACTS_WITH", "rel1_IS_A", "rel1_ISA", "rel1_LOCATION_OF", "rel1_lower_than", "rel1_MANIFESTATION_OF", "rel1_METHOD_OF", "rel1_OCCURS_IN", "rel1_PART_OF", "rel1_PRECEDES", "rel1_PREDISPOSES", "rel1_PREVENTS", "rel1_PROCESS_OF", "rel1_PRODUCES", "rel1_same_as", "rel1_STIMULATES", "rel1_TREATS", "rel1_USES", "rel1_MENTIONED_IN", "rel1_HAS_MESH", "nod2_aapp", "nod2_acab", "nod2_acty", "nod2_aggp", "nod2_amas", "nod2_amph", "nod2_anab", "nod2_anim", "nod2_anst", "nod2_antb", "nod2_arch", "nod2_bacs", "nod2_bact", "nod2_bdsu", "nod2_bdsy", "nod2_bhvr", "nod2_biof", "nod2_bird", "nod2_blor", "nod2_bmod", "nod2_bodm", "nod2_bpoc", "nod2_bsoj", "nod2_celc", "nod2_celf", "nod2_cell", "nod2_cgab", "nod2_chem", "nod2_chvf", "nod2_chvs", "nod2_clas", "nod2_clna", "nod2_clnd", "nod2_cnce", "nod2_comd", "nod2_crbs", "nod2_diap", "nod2_dora", "nod2_drdd", "nod2_dsyn", "nod2_edac", "nod2_eehu", "nod2_elii", "nod2_emod", "nod2_emst", "nod2_enty", "nod2_enzy", "nod2_euka", "nod2_evnt", "nod2_famg", "nod2_ffas", "nod2_fish", "nod2_fndg", "nod2_fngs", "nod2_food", "nod2_ftcn", "nod2_genf", "nod2_geoa", "nod2_gngm", "nod2_gora", "nod2_grpa", "nod2_grup", "nod2_hcpp", "nod2_hcro", "nod2_hlca", "nod2_hops", "nod2_horm", "nod2_humn", "nod2_idcn", "nod2_imft", "nod2_inbe", "nod2_inch", "nod2_inpo", "nod2_inpr", "nod2_irda", "nod2_lang", "nod2_lbpr", "nod2_lbtr", "nod2_mamm", "nod2_mbrt", "nod2_mcha", "nod2_medd", "nod2_menp", "nod2_mnob", "nod2_mobd", "nod2_moft", "nod2_mosq", "nod2_neop", "nod2_nnon", "nod2_npop", "nod2_nusq", "nod2_ocac", "nod2_ocdi", "nod2_orch", "nod2_orga", "nod2_orgf", "nod2_orgm", "nod2_orgt", "nod2_ortf", "nod2_patf", "nod2_phob", "nod2_phpr", "nod2_phsf", "nod2_phsu", "nod2_plnt", "nod2_podg", "nod2_popg", "nod2_prog", "nod2_pros", "nod2_qlco", "nod2_qnco", "nod2_rcpt", "nod2_rept", "nod2_resa", "nod2_resd", "nod2_rnlw", "nod2_sbst", "nod2_shro", "nod2_socb", "nod2_sosy", "nod2_spco", "nod2_tisu", "nod2_tmco", "nod2_topp", "nod2_virs", "nod2_vita", "nod2_vtbt", "rel2_ADMINISTERED_TO", "rel2_AFFECTS", "rel2_ASSOCIATED_WITH", "rel2_AUGMENTS", "rel2_CAUSES", "rel2_COEXISTS_WITH", "rel2_compared_with", "rel2_COMPLICATES", "rel2_CONVERTS_TO", "rel2_DIAGNOSES", "rel2_different_from", "rel2_different_than", "rel2_DISRUPTS", "rel2_higher_than", "rel2_INHIBITS", "rel2_INTERACTS_WITH", "rel2_IS_A", "rel2_ISA", "rel2_LOCATION_OF", "rel2_lower_than", "rel2_MANIFESTATION_OF", "rel2_METHOD_OF", "rel2_OCCURS_IN", "rel2_PART_OF", "rel2_PRECEDES", "rel2_PREDISPOSES", "rel2_PREVENTS", "rel2_PROCESS_OF", "rel2_PRODUCES", "rel2_same_as", "rel2_STIMULATES", "rel2_TREATS", "rel2_USES", "rel2_MENTIONED_IN", "rel2_HAS_MESH", "nod3_aapp", "nod3_acab", "nod3_acty", "nod3_aggp", "nod3_amas", "nod3_amph", "nod3_anab", "nod3_anim", "nod3_anst", "nod3_antb", "nod3_arch", "nod3_bacs", "nod3_bact", "nod3_bdsu", "nod3_bdsy", "nod3_bhvr", "nod3_biof", "nod3_bird", "nod3_blor", "nod3_bmod", "nod3_bodm", "nod3_bpoc", "nod3_bsoj", "nod3_celc", "nod3_celf", "nod3_cell", "nod3_cgab", "nod3_chem", "nod3_chvf", "nod3_chvs", "nod3_clas", "nod3_clna", "nod3_clnd", "nod3_cnce", "nod3_comd", "nod3_crbs", "nod3_diap", "nod3_dora", "nod3_drdd", "nod3_dsyn", "nod3_edac", "nod3_eehu", "nod3_elii", "nod3_emod", "nod3_emst", "nod3_enty", "nod3_enzy", "nod3_euka", "nod3_evnt", "nod3_famg", "nod3_ffas", "nod3_fish", "nod3_fndg", "nod3_fngs", "nod3_food", "nod3_ftcn", "nod3_genf", "nod3_geoa", "nod3_gngm", "nod3_gora", "nod3_grpa", "nod3_grup", "nod3_hcpp", "nod3_hcro", "nod3_hlca", "nod3_hops", "nod3_horm", "nod3_humn", "nod3_idcn", "nod3_imft", "nod3_inbe", "nod3_inch", "nod3_inpo", "nod3_inpr", "nod3_irda", "nod3_lang", "nod3_lbpr", "nod3_lbtr", "nod3_mamm", "nod3_mbrt", "nod3_mcha", "nod3_medd", "nod3_menp", "nod3_mnob", "nod3_mobd", "nod3_moft", "nod3_mosq", "nod3_neop", "nod3_nnon", "nod3_npop", "nod3_nusq", "nod3_ocac", "nod3_ocdi", "nod3_orch", "nod3_orga", "nod3_orgf", "nod3_orgm", "nod3_orgt", "nod3_ortf", "nod3_patf", "nod3_phob", "nod3_phpr", "nod3_phsf", "nod3_phsu", "nod3_plnt", "nod3_podg", "nod3_popg", "nod3_prog", "nod3_pros", "nod3_qlco", "nod3_qnco", "nod3_rcpt", "nod3_rept", "nod3_resa", "nod3_resd", "nod3_rnlw", "nod3_sbst", "nod3_shro", "nod3_socb", "nod3_sosy", "nod3_spco", "nod3_tisu", "nod3_tmco", "nod3_topp", "nod3_virs", "nod3_vita", "nod3_vtbt", "rel3_ADMINISTERED_TO", "rel3_AFFECTS", "rel3_ASSOCIATED_WITH", "rel3_AUGMENTS", "rel3_CAUSES", "rel3_COEXISTS_WITH", "rel3_compared_with", "rel3_COMPLICATES", "rel3_CONVERTS_TO", "rel3_DIAGNOSES", "rel3_different_from", "rel3_different_than", "rel3_DISRUPTS", "rel3_higher_than", "rel3_INHIBITS", "rel3_INTERACTS_WITH", "rel3_IS_A", "rel3_ISA", "rel3_LOCATION_OF", "rel3_lower_than", "rel3_MANIFESTATION_OF", "rel3_METHOD_OF", "rel3_OCCURS_IN", "rel3_PART_OF", "rel3_PRECEDES", "rel3_PREDISPOSES", "rel3_PREVENTS", "rel3_PROCESS_OF", "rel3_PRODUCES", "rel3_same_as", "rel3_STIMULATES", "rel3_TREATS", "rel3_USES", "rel3_MENTIONED_IN", "rel3_HAS_MESH", "PATH0", "PATH1", "PATH2", "PATH3", "PATH4", "PATH5", "PATH6", "PATH7", "PATH8", "PATH9", "PATH10", "PATH11", "PATH12", "PATH13", "PATH14", "PATH15", "PATH16", "PATH17", "PATH18", "PATH19", "PATH20", "PATH21", "PATH22", "PATH23", "PATH24", "PATH25", "PATH26", "PATH27", "PATH28", "PATH29", "PATH30", "PATH31", "PATH32", "PATH33", "PATH34", "PATH35", "PATH36", "PATH37", "PATH38", "PATH39", "PATH40", "PATH41", "PATH42", "PATH43", "PATH44", "PATH45", "PATH46", "PATH47", "PATH48", "PATH49", "PATH50", "PATH51", "PATH52", "PATH53", "PATH54", "PATH55", "PATH56", "PATH57", "PATH58", "PATH59", "PATH60", "PATH61", "PATH62", "PATH63", "PATH64", "PATH65", "PATH66", "PATH67", "PATH68", "PATH69", "PATH70", "PATH71", "PATH72", "PATH73", "PATH74", "PATH75", "PATH76", "PATH77", "PATH78", "PATH79", "PATH80", "PATH81", "PATH82", "PATH83", "PATH84", "PATH85", "PATH86", "PATH87", "PATH88", "PATH89", "PATH90", "PATH91", "PATH92", "PATH93", "PATH94", "PATH95", "PATH96", "PATH97", "PATH98", "PATH99"]

   X=data[feature_cols]
   y=data["GROUNDTRUTH"]

   # create model
   print('create model...')
   #Create a RF Classifier
   model=RandomForestClassifier(n_estimators=100)

   #undersampling
   undersample = RandomUnderSampler(sampling_strategy=0.1)
   X, y = undersample.fit_resample(X, y)
   print('Negative, Positive samples: ',Counter(y))

   header=[["nod1_aapp", "nod1_acab", "nod1_acty", "nod1_aggp", "nod1_amas", "nod1_amph", "nod1_anab", "nod1_anim", "nod1_anst", "nod1_antb", "nod1_arch", "nod1_bacs", "nod1_bact", "nod1_bdsu", "nod1_bdsy", "nod1_bhvr", "nod1_biof", "nod1_bird", "nod1_blor", "nod1_bmod", "nod1_bodm", "nod1_bpoc", "nod1_bsoj", "nod1_celc", "nod1_celf", "nod1_cell", "nod1_cgab", "nod1_chem", "nod1_chvf", "nod1_chvs", "nod1_clas", "nod1_clna", "nod1_clnd", "nod1_cnce", "nod1_comd", "nod1_crbs", "nod1_diap", "nod1_dora", "nod1_drdd", "nod1_dsyn", "nod1_edac", "nod1_eehu", "nod1_elii", "nod1_emod", "nod1_emst", "nod1_enty", "nod1_enzy", "nod1_euka", "nod1_evnt", "nod1_famg", "nod1_ffas", "nod1_fish", "nod1_fndg", "nod1_fngs", "nod1_food", "nod1_ftcn", "nod1_genf", "nod1_geoa", "nod1_gngm", "nod1_gora", "nod1_grpa", "nod1_grup", "nod1_hcpp", "nod1_hcro", "nod1_hlca", "nod1_hops", "nod1_horm", "nod1_humn", "nod1_idcn", "nod1_imft", "nod1_inbe", "nod1_inch", "nod1_inpo", "nod1_inpr", "nod1_irda", "nod1_lang", "nod1_lbpr", "nod1_lbtr", "nod1_mamm", "nod1_mbrt", "nod1_mcha", "nod1_medd", "nod1_menp", "nod1_mnob", "nod1_mobd", "nod1_moft", "nod1_mosq", "nod1_neop", "nod1_nnon", "nod1_npop", "nod1_nusq", "nod1_ocac", "nod1_ocdi", "nod1_orch", "nod1_orga", "nod1_orgf", "nod1_orgm", "nod1_orgt", "nod1_ortf", "nod1_patf", "nod1_phob", "nod1_phpr", "nod1_phsf", "nod1_phsu", "nod1_plnt", "nod1_podg", "nod1_popg", "nod1_prog", "nod1_pros", "nod1_qlco", "nod1_qnco", "nod1_rcpt", "nod1_rept", "nod1_resa", "nod1_resd", "nod1_rnlw", "nod1_sbst", "nod1_shro", "nod1_socb", "nod1_sosy", "nod1_spco", "nod1_tisu", "nod1_tmco", "nod1_topp", "nod1_virs", "nod1_vita", "nod1_vtbt", "rel1_ADMINISTERED_TO", "rel1_AFFECTS", "rel1_ASSOCIATED_WITH", "rel1_AUGMENTS", "rel1_CAUSES", "rel1_COEXISTS_WITH", "rel1_compared_with", "rel1_COMPLICATES", "rel1_CONVERTS_TO", "rel1_DIAGNOSES", "rel1_different_from", "rel1_different_than", "rel1_DISRUPTS", "rel1_higher_than", "rel1_INHIBITS", "rel1_INTERACTS_WITH", "rel1_IS_A", "rel1_ISA", "rel1_LOCATION_OF", "rel1_lower_than", "rel1_MANIFESTATION_OF", "rel1_METHOD_OF", "rel1_OCCURS_IN", "rel1_PART_OF", "rel1_PRECEDES", "rel1_PREDISPOSES", "rel1_PREVENTS", "rel1_PROCESS_OF", "rel1_PRODUCES", "rel1_same_as", "rel1_STIMULATES", "rel1_TREATS", "rel1_USES", "rel1_MENTIONED_IN", "rel1_HAS_MESH", "rel1_LITERATURE_DTI", "nod2_aapp", "nod2_acab", "nod2_acty", "nod2_aggp", "nod2_amas", "nod2_amph", "nod2_anab", "nod2_anim", "nod2_anst", "nod2_antb", "nod2_arch", "nod2_bacs", "nod2_bact", "nod2_bdsu", "nod2_bdsy", "nod2_bhvr", "nod2_biof", "nod2_bird", "nod2_blor", "nod2_bmod", "nod2_bodm", "nod2_bpoc", "nod2_bsoj", "nod2_celc", "nod2_celf", "nod2_cell", "nod2_cgab", "nod2_chem", "nod2_chvf", "nod2_chvs", "nod2_clas", "nod2_clna", "nod2_clnd", "nod2_cnce", "nod2_comd", "nod2_crbs", "nod2_diap", "nod2_dora", "nod2_drdd", "nod2_dsyn", "nod2_edac", "nod2_eehu", "nod2_elii", "nod2_emod", "nod2_emst", "nod2_enty", "nod2_enzy", "nod2_euka", "nod2_evnt", "nod2_famg", "nod2_ffas", "nod2_fish", "nod2_fndg", "nod2_fngs", "nod2_food", "nod2_ftcn", "nod2_genf", "nod2_geoa", "nod2_gngm", "nod2_gora", "nod2_grpa", "nod2_grup", "nod2_hcpp", "nod2_hcro", "nod2_hlca", "nod2_hops", "nod2_horm", "nod2_humn", "nod2_idcn", "nod2_imft", "nod2_inbe", "nod2_inch", "nod2_inpo", "nod2_inpr", "nod2_irda", "nod2_lang", "nod2_lbpr", "nod2_lbtr", "nod2_mamm", "nod2_mbrt", "nod2_mcha", "nod2_medd", "nod2_menp", "nod2_mnob", "nod2_mobd", "nod2_moft", "nod2_mosq", "nod2_neop", "nod2_nnon", "nod2_npop", "nod2_nusq", "nod2_ocac", "nod2_ocdi", "nod2_orch", "nod2_orga", "nod2_orgf", "nod2_orgm", "nod2_orgt", "nod2_ortf", "nod2_patf", "nod2_phob", "nod2_phpr", "nod2_phsf", "nod2_phsu", "nod2_plnt", "nod2_podg", "nod2_popg", "nod2_prog", "nod2_pros", "nod2_qlco", "nod2_qnco", "nod2_rcpt", "nod2_rept", "nod2_resa", "nod2_resd", "nod2_rnlw", "nod2_sbst", "nod2_shro", "nod2_socb", "nod2_sosy", "nod2_spco", "nod2_tisu", "nod2_tmco", "nod2_topp", "nod2_virs", "nod2_vita", "nod2_vtbt", "rel2_ADMINISTERED_TO", "rel2_AFFECTS", "rel2_ASSOCIATED_WITH", "rel2_AUGMENTS", "rel2_CAUSES", "rel2_COEXISTS_WITH", "rel2_compared_with", "rel2_COMPLICATES", "rel2_CONVERTS_TO", "rel2_DIAGNOSES", "rel2_different_from", "rel2_different_than", "rel2_DISRUPTS", "rel2_higher_than", "rel2_INHIBITS", "rel2_INTERACTS_WITH", "rel2_IS_A", "rel2_ISA", "rel2_LOCATION_OF", "rel2_lower_than", "rel2_MANIFESTATION_OF", "rel2_METHOD_OF", "rel2_OCCURS_IN", "rel2_PART_OF", "rel2_PRECEDES", "rel2_PREDISPOSES", "rel2_PREVENTS", "rel2_PROCESS_OF", "rel2_PRODUCES", "rel2_same_as", "rel2_STIMULATES", "rel2_TREATS", "rel2_USES", "rel2_MENTIONED_IN", "rel2_HAS_MESH", "rel2_LITERATURE_DTI", "nod3_aapp", "nod3_acab", "nod3_acty", "nod3_aggp", "nod3_amas", "nod3_amph", "nod3_anab", "nod3_anim", "nod3_anst", "nod3_antb", "nod3_arch", "nod3_bacs", "nod3_bact", "nod3_bdsu", "nod3_bdsy", "nod3_bhvr", "nod3_biof", "nod3_bird", "nod3_blor", "nod3_bmod", "nod3_bodm", "nod3_bpoc", "nod3_bsoj", "nod3_celc", "nod3_celf", "nod3_cell", "nod3_cgab", "nod3_chem", "nod3_chvf", "nod3_chvs", "nod3_clas", "nod3_clna", "nod3_clnd", "nod3_cnce", "nod3_comd", "nod3_crbs", "nod3_diap", "nod3_dora", "nod3_drdd", "nod3_dsyn", "nod3_edac", "nod3_eehu", "nod3_elii", "nod3_emod", "nod3_emst", "nod3_enty", "nod3_enzy", "nod3_euka", "nod3_evnt", "nod3_famg", "nod3_ffas", "nod3_fish", "nod3_fndg", "nod3_fngs", "nod3_food", "nod3_ftcn", "nod3_genf", "nod3_geoa", "nod3_gngm", "nod3_gora", "nod3_grpa", "nod3_grup", "nod3_hcpp", "nod3_hcro", "nod3_hlca", "nod3_hops", "nod3_horm", "nod3_humn", "nod3_idcn", "nod3_imft", "nod3_inbe", "nod3_inch", "nod3_inpo", "nod3_inpr", "nod3_irda", "nod3_lang", "nod3_lbpr", "nod3_lbtr", "nod3_mamm", "nod3_mbrt", "nod3_mcha", "nod3_medd", "nod3_menp", "nod3_mnob", "nod3_mobd", "nod3_moft", "nod3_mosq", "nod3_neop", "nod3_nnon", "nod3_npop", "nod3_nusq", "nod3_ocac", "nod3_ocdi", "nod3_orch", "nod3_orga", "nod3_orgf", "nod3_orgm", "nod3_orgt", "nod3_ortf", "nod3_patf", "nod3_phob", "nod3_phpr", "nod3_phsf", "nod3_phsu", "nod3_plnt", "nod3_podg", "nod3_popg", "nod3_prog", "nod3_pros", "nod3_qlco", "nod3_qnco", "nod3_rcpt", "nod3_rept", "nod3_resa", "nod3_resd", "nod3_rnlw", "nod3_sbst", "nod3_shro", "nod3_socb", "nod3_sosy", "nod3_spco", "nod3_tisu", "nod3_tmco", "nod3_topp", "nod3_virs", "nod3_vita", "nod3_vtbt", "rel3_ADMINISTERED_TO", "rel3_AFFECTS", "rel3_ASSOCIATED_WITH", "rel3_AUGMENTS", "rel3_CAUSES", "rel3_COEXISTS_WITH", "rel3_compared_with", "rel3_COMPLICATES", "rel3_CONVERTS_TO", "rel3_DIAGNOSES", "rel3_different_from", "rel3_different_than", "rel3_DISRUPTS", "rel3_higher_than", "rel3_INHIBITS", "rel3_INTERACTS_WITH", "rel3_IS_A", "rel3_ISA", "rel3_LOCATION_OF", "rel3_lower_than", "rel3_MANIFESTATION_OF", "rel3_METHOD_OF", "rel3_OCCURS_IN", "rel3_PART_OF", "rel3_PRECEDES", "rel3_PREDISPOSES", "rel3_PREVENTS", "rel3_PROCESS_OF", "rel3_PRODUCES", "rel3_same_as", "rel3_STIMULATES", "rel3_TREATS", "rel3_USES", "rel3_MENTIONED_IN", "rel3_HAS_MESH", "rel3_LITERATURE_DTI", "PATH0", "PATH1", "PATH2", "PATH3", "PATH4", "PATH5", "PATH6", "PATH7", "PATH8", "PATH9", "PATH10", "PATH11", "PATH12", "PATH13", "PATH14", "PATH15", "PATH16", "PATH17", "PATH18", "PATH19", "PATH20", "PATH21", "PATH22", "PATH23", "PATH24", "PATH25", "PATH26", "PATH27", "PATH28", "PATH29", "PATH30", "PATH31", "PATH32", "PATH33", "PATH34", "PATH35", "PATH36", "PATH37", "PATH38", "PATH39", "PATH40", "PATH41", "PATH42", "PATH43", "PATH44", "PATH45", "PATH46", "PATH47", "PATH48", "PATH49", "PATH50", "PATH51", "PATH52", "PATH53", "PATH54", "PATH55", "PATH56", "PATH57", "PATH58", "PATH59", "PATH60", "PATH61", "PATH62", "PATH63", "PATH64", "PATH65", "PATH66", "PATH67", "PATH68", "PATH69", "PATH70", "PATH71", "PATH72", "PATH73", "PATH74", "PATH75", "PATH76", "PATH77", "PATH78", "PATH79", "PATH80", "PATH81", "PATH82", "PATH83", "PATH84", "PATH85", "PATH86", "PATH87", "PATH88", "PATH89", "PATH90", "PATH91", "PATH92", "PATH93", "PATH94", "PATH95", "PATH96", "PATH97", "PATH98", "PATH99"]]
   X_train, X_test, y_train, y_test = train_test_split( X, y, test_size=0.1, random_state=42)         
   undersample2 = RandomUnderSampler(sampling_strategy=0.2)
   X_train, y_train = undersample2.fit_resample(X_train, y_train)
   model.fit(X_train, y_train)
   #model.fit(X, y)
   
      ####SelectFrom Model
   print('Create SelectFrom Model...')
   sfm = SelectFromModel(model,threshold=0.0033) #0.004, prefit=True)
   print(' Train the selector')
   sfm.fit(X_train, y_train)
   #sfm.fit(X,y)
   X_important_train = sfm.transform(X_train)
   X_important_test = sfm.transform(X_test)
   X_important = sfm.transform(X)
   header_important = sfm.transform(header)

   # prepare the cross-validation procedure
   print('prepare the cross-validation procedure...')
   cv = StratifiedKFold(n_splits=10, random_state=1, shuffle=True)
   # evaluate model
   print('evaluate model...')

   result, testdt_X, testdt_y = tenFoldCV(X_important, y, cv, model, header_important)

   print("10-fold CV finished...calculating macro avg  ")
      
   # report RANDOM FOREST performance
   print('Precision: %.3f ' % (result['Precision']))
   print('Recall: %.3f ' % (result['Recall']))
   print('f1-score: %.3f ' % (result['f1score']))
   

   ###pre-pruning
   dt1 = DecisionTreeClassifier()
   from sklearn import tree
   from sklearn.model_selection import GridSearchCV
   grid_param={
      "criterion":["gini","entropy"],
      #"splitter":["best","random"],
      "min_impurity_decrease":[x * 0.0001 for x in range(1, 10)],
      #"min_samples_leaf":range(5,15,1),
      #"min_samples_split":range(10,15,1) 
   }
   grid_search=GridSearchCV(estimator=dt1,param_grid=grid_param,cv=5,n_jobs=None)
   grid_search.fit(testdt_X, testdt_y)
   params=grid_search.best_params_
   print(params)
   dt = DecisionTreeClassifier(criterion=params['criterion'],min_impurity_decrease= params['min_impurity_decrease'],min_samples_split= 10,splitter= 'random')

   d='pre-pruned'

#   dt = DecisionTreeClassifier(criterion= 'entropy', min_impurity_decrease = 0.0003, min_samples_split= 10,splitter= 'random')

   ###post-pruning
   path=dt.cost_complexity_pruning_path(testdt_X, testdt_y)
   ####path variable gives two things ccp_alphas and impurities
   ccp_alphas,impurities=path.ccp_alphas,path.impurities
   print("Post pruning Decision Tree...ccp alpha wil give list of values :",ccp_alphas)
   print("***********************************************************")
   print("Impurities in Decision Tree :",impurities)
   clfs=[]   #will store all the models here
   t=0
   for ccp_alpha in ccp_alphas:
       dt_p=DecisionTreeClassifier(random_state=0,ccp_alpha=ccp_alpha)
       dt_p.fit(testdt_X, testdt_y)
       clfs.append(dt_p)
       #print("Last node in Decision tree is {} and ccp_alpha for last node is {}".format(clfs[-1].tree_.node_count,ccp_alphas[-1]))
       preddt_y = dt_p.predict(testdt_X)
       f1 = metrics.f1_score(testdt_y, preddt_y)
       print("Tree ", t," f1_score ", f1, "and accuracy: "+str(dt_p.score(testdt_X, testdt_y)))
       if (f1<0.86):
          break
       if (dt_p.get_depth()<8):
          saveTree(dt_p, header_important[0], t)
       t=t+1

   #acc_scores = [clf.score(testdt_X, testdt_y) for clf in clfs]
   #print("acc_scores ", acc_scores)
   
   
   dt.fit(testdt_X, testdt_y)
   preddt_y= dt.predict(testdt_X)
   train_accuracy=metrics.accuracy_score(testdt_y, preddt_y)
   train_f1=metrics.f1_score(testdt_y, preddt_y)
   print("Decision tree with no post-pruning -> accuracy: ", train_accuracy, "f1-score: ", train_f1)
  
   saveTree(dt, header_important[0], 'no-pp') 

main()
