import os
import glob
import time

import pickle
import string
import numpy as np
from sklearn.metrics import classification_report, precision_recall_fscore_support, roc_auc_score, average_precision_score, precision_recall_curve
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from  nltk.corpus import stopwords
from lenskit import topn
import time
import torch.nn.functional as F
import re
from unidecode import unidecode

import warnings
from sklearn.exceptions import UndefinedMetricWarning
warnings.filterwarnings(action='ignore', category=UndefinedMetricWarning)

pd.set_option("display.precision", 4)

# Calculate BERTScore
def bertscore(emb_true, emb_pred):
    
    sim = cosine_similarity(emb_true, emb_pred)
    rec = sim.max(-1).mean()
    pre = sim.max(0).mean()
    f1 = 2 * rec * pre / (rec + pre + 1e-7)
    return pre, rec, f1

# Calculate  BERT score in test sentences
def get_sentence_bert_score(word_df, label, sent_pred, sent_true, wordvectors, 
                            sent_thresh, tag_thresh, syn = True):
    
    # get sentence-wise BERT score
    metric_df = []
    cols = ["pmid", "sid","sent_t","sent_p","rank", "bert_pre", "bert_rec", "bert_f1"]
    
    for idx, temp_df in word_df.groupby("idx"):
        
        bert_metric = [sent_pred["pmid"].loc[idx], 
                       sent_pred["sid"].loc[idx], 
                       sent_true[label].loc[idx],
                       sent_pred[label].loc[idx],
                       sent_pred["rank"].loc[idx]] 
        
        words_true = temp_df[ (temp_df.tag_t == 1) ][["tid","wid","word","token"]]
        emb_true = wordvectors[idx][words_true.tid.values]
        
        if syn:
            words_pred = temp_df[(temp_df.sent_p >= sent_thresh) & (temp_df.tag_p >= tag_thresh) ][["tid","sid","wid","word","token"]]
            #temp_df.loc[words_pred.index,"tag_p_binary"] = 1
        else:
            words_pred = temp_df[ (temp_df.tag_p >= tag_thresh) ][["tid","sid","wid","word","token"]]
        
        emb_pred = wordvectors[idx][words_pred.tid.values]
    
        # bert score
        if len(emb_true) > 0 and  len(emb_pred) > 0:
            bert_pre, bert_rec, bert_f1 = bertscore(emb_true, emb_pred)
            
        elif len(emb_true) > 0 and  len(emb_pred) == 0:
            bert_pre = None
            bert_rec = 0
            bert_f1 = 0
            
        elif len(emb_true) == 0 and len(temp_df[temp_df.sent_p > sent_thresh])>0:     # wrong prediction of sentence, no matter if a token is predicted
            bert_pre = 0
            bert_rec = None
            bert_f1 = 0           
            
        else:
            bert_pre = bert_rec = bert_f1 = None
            
        metric_df.append(bert_metric + [bert_pre, bert_rec, bert_f1])
        
    metric_df = pd.DataFrame(metric_df, columns = cols)    
    
    return metric_df

# Calculate top-k metrics    
def tag_metric_at_k(all_df, wv, sent_thresh = 0.5, tag_thresh = 0.5, k = 1):

    # How to determine truth: 
    # If len(predicted sentence) < k and len(true sentence) >=k, 
    # make k true sentences incuding the predicted ones and randomly selected true ones
    # precision/recall is done within the k sentences
    
    # set item as the concatenated sid + tid
    all_df["item"] = all_df["sid"].astype(str) + "-" + all_df["tid"].astype(str)
    
    # try best match the true sentences with topk 
    temp_true = all_df[["pmid","sid","sent_t","rank"]].drop_duplicates().sort_values(by = ["sent_t", "rank"], ascending = [False, True]).groupby("pmid").head(k)
     
    # set selected sentences as Truth
    temp_true = temp_true[["pmid","sid"]].merge(all_df, on = ["pmid","sid"])
    temp_true = temp_true[temp_true.tag_t == 1]
    
     # set predicted tokens by threshold
    temp_pred = all_df[ (all_df["rank"] <= k ) & (all_df["sent_p"] >= sent_thresh) & (all_df["tag_p"] >= tag_thresh)]
    
    if len(temp_pred) > 0:
        # topn is set to the length of true tokens
        rla = topn.RecListAnalysis(group_cols = ["pmid"])
        rla.add_metric(topn.precision)
        rla.add_metric(topn.recall)

        results = rla.compute(temp_pred[["pmid","item"]], temp_true[["pmid","item"]], include_missing = True )
        
        nrecs = temp_pred.groupby("pmid").size()
        results = pd.concat([results[["precision","recall"]], nrecs], axis = 1 )
        
        ntruth = temp_true.groupby("pmid").size()
        results = pd.concat([results, ntruth], axis = 1 )
        results.columns = ["precision","recall", 'nrecs', 'ntruth']
        
        results["nrecs"] = results["nrecs"].fillna(0)
        results['ntruth'] = results['ntruth'].fillna(0)

        # if truth exists while no prediction (NAN), set precision/recall to 0
        results.loc[(results.nrecs == 0) & (results.ntruth > 0), "recall"] = 0
        
        # if truth does not exists while prediction exists (precision = NAN), set precision to 0
        results.loc[(results.nrecs > 0) & (results.ntruth == 0), "precision"] = 0
        
        # compute f1
        #results['f1'] = np.nan
        #results.loc[(results.precision>0) & (results.recall>0), "f1" ] = 2 * (results["precision"] * results["recall"])/( results["precision"] + results["recall"] )
        #results.loc[(results.precision == 0) | (results.recall == 0), "f1" ] = 0
        
        # Calculate bert score
    
        recall_by_words = pd.DataFrame([])
        
        for (pmid, idx), d in temp_true.groupby(["pmid","idx"]):
            emb_true = wv[idx][d.tid.values]
            
            pred_tids = d[(d["rank"]<=k) & (d.sent_p >= sent_thresh) & (d.tag_p >= tag_thresh)].tid.values
            emb_pred = wv[idx][pred_tids]
            
            if len(emb_true) > 0:
                if len(emb_pred) > 0:
                    rec = cosine_similarity(emb_true, emb_pred).max(axis = 1)
                else:                # no words recalled
                    rec = np.zeros(len(emb_true))
                
                rec = pd.DataFrame({"pmid": pmid, "idx":idx, "bert_rec": rec})
                recall_by_words = pd.concat([recall_by_words, rec], axis = 0, ignore_index= True)
                
        precision_by_words = pd.DataFrame([])
        
        for (pmid, idx), d in temp_pred.groupby(["pmid","idx"]):
            true_tids = d[d.tag_t==1].tid.values
            emb_true = wv[idx][true_tids]
            
            emb_pred = wv[idx][d.tid.values]
            
            if len(emb_pred) > 0:
                if len(emb_true) > 0:
                    prec = cosine_similarity(emb_true, emb_pred).max(axis = 0)
                else:                # no words recalled
                    prec = np.zeros(len(emb_pred))
                
                prec = pd.DataFrame({"pmid": pmid, "idx":idx, "bert_pre": prec})
                precision_by_words = pd.concat([precision_by_words, prec], axis = 0, ignore_index= True)
                
        bert_prec = precision_by_words.groupby("pmid")["bert_pre"].mean()
        results = pd.concat([results, bert_prec], axis = 1)
        
        bert_rec = recall_by_words.groupby("pmid")["bert_rec"].mean()
        results = pd.concat([results, bert_rec], axis = 1)
            
    else:
        results = None
        print("Something wrong here. No prediction made")
    
    return results

# Collect all tokens for predicted and ground truth sentences
def get_token_df(alignment, remove_stop = False, stop_words = None,
                      remove_punct = False):
    
    all_df = pd.DataFrame([])
    
    for i, a in enumerate(alignment):
        
        df = pd.DataFrame.from_dict(a, orient="index").reset_index()
        df.columns =  ["tid", "wid", "word","token"]
        df['idx'] = i
        
        all_df = pd.concat([all_df, df], axis = 0, ignore_index = True)
        
    if remove_punct:
        all_df = all_df[~all_df.word.isin(list(string.punctuation))]

    if remove_stop:
        all_df = all_df[~all_df.word.isin(stop_words)]
    
    return all_df

# Get predicted tokens and ground truth for a label
def get_token_df_for_label(token_df, label, sent_true, sent_pred, 
                      tag_true, tag_pred):
    
    # merge token_df with sent_pred
    temp = sent_pred[["pmid","sid","rank",label]].rename({label: 'sent_p'}, axis = 1)
    token_df = pd.merge(token_df, temp, left_on='idx', right_index=True)

    # merge token_df with sent_pred
    temp = sent_true[[label]].rename({label: 'sent_t'}, axis = 1)
    token_df = pd.merge(token_df, temp, left_on='idx', right_index=True)
    #print(token_df.head())
    
    token_df['tag_p'] = 0
    token_df['tag_t'] = 0
    for idx, df in token_df.groupby("idx"):
        token_df.loc[token_df.idx== idx, 'tag_p'] = tag_pred[label][idx][df.tid.values]
        token_df.loc[token_df.idx== idx, 'tag_t'] = tag_true[label][idx][df.tid.values] * sent_true[label].loc[idx]
    
    return token_df

# Calculate a classification metrics for top-K 
def classify_metric_at_k(sent_true, sent_pred, label, sent_thresh = 0.5, k=1):
    
    # calculate recall as the % of true sentences in the predicted top_k 
    # precision as the % of the predicted topk sentences is true
    
    # get all cols collected
    temp = sent_pred[["pmid","sid","rank",label]].copy()
    temp = temp.rename({label: "pred"}, axis = 1)
    temp = sent_true[["pmid","sid",label]].merge(temp[["pmid","sid","rank","pred"]], on = ["pmid","sid"])
    
    # rename sid to "item"
    temp = temp.rename({"sid":"item"}, axis = 1)
    
    # get the maximum possible matching between prediction and truth
    temp_true = temp.sort_values(by = [label, "rank"], ascending = [False,True]).groupby("pmid").head(k)
    temp_true = temp_true[temp_true[label]==1][["pmid","item"]]

    temp_pred = temp[(temp["pred"]>=sent_thresh) & (temp["rank"]<=k)][["pmid","item"]]
    
    
    if len(temp_pred) > 0 and len(temp_true) > 0:
        rla = topn.RecListAnalysis(group_cols = ["pmid"])
        rla.add_metric(topn.precision)
        rla.add_metric(topn.recall)
        results = rla.compute(temp_pred[["pmid","item"]], temp_true[["pmid","item"]], include_missing = True)
        
        nrecs = temp_pred.groupby("pmid").size()
        results = pd.concat([results[["precision","recall"]], nrecs], axis = 1 )
        
        ntruth = temp_true.groupby("pmid").size()
        results = pd.concat([results, ntruth], axis = 1 )
        results.columns = ["precision","recall", 'nrecs', 'ntruth']
        
        results["nrecs"] = results["nrecs"].fillna(0)
        results['ntruth'] = results['ntruth'].fillna(0)

        # set recall to 0 if truth exists while no prediction provided
        results.loc[(results.nrecs == 0) & (results.ntruth > 0), "recall"] = 0
        
        # set precision to 0 if truth does not exist while predictions exist
        results.loc[(results.nrecs > 0) & (results.ntruth == 0), "precision"] = 0
        
        # calculate f1
        results['f1'] = np.nan
        results.loc[(results.precision>0) & (results.recall>0), "f1" ] = 2 * (results["precision"] * results["recall"])/( results["precision"] + results["recall"] )
        results.loc[(results.precision == 0) | (results.recall == 0), "f1" ] = 0

    else:
        results = None
        print("Something wrong here. No prediction made")
    
    return results

                                         
 # Calculate classification and tagging performance   
def classify_tag_metrics(label, sent_true, sent_pred, 
                      token_df = None, tag_true = None, tag_pred = None,
                      wordvectors = None, topk = 3,
                      syn = True,
                      sent_thresh = 0.5,
                      tag_thresh = 0.5,
                      for_correct_sentences = False,
                      tagging = True):
        
    all_df = pd.DataFrame([])
    metric_article = None
    metric_overall = {}
    bert_metric_df = None
    
    #print(sent_pred.head())
    start_time = time.time()
    # rank sent_pred so top-k result can be obtained later
    
    sent_pred["rank"] = sent_pred.groupby("pmid")[label].rank(method="first", ascending=False)
    
    # sentence classification
    metrics_classifier = pd.DataFrame([])

    for k in [1, topk, 10000]:  # 10000 means all sentences

        suffix = "_"+str(k) if k<10000 else ''
        
        
        metrics = classify_metric_at_k(sent_true, sent_pred, label, sent_thresh = sent_thresh, k=k)

        if metrics is not None:
            metrics = metrics[["precision","recall", "f1"]]
            metrics.columns = ["p"+suffix,'r'+suffix, 'f1'+suffix]
            metrics_classifier = pd.concat([metrics_classifier, metrics], axis = 1)
        
    metrics_classifier = metrics_classifier.reset_index()
    
    # overall auc prc
    auc = roc_auc_score(sent_true[label], sent_pred[label])
    prc = average_precision_score(sent_true[label], sent_pred[label])
    
    p,r, f1,_ = precision_recall_fscore_support(sent_true[label], (sent_pred[label] > sent_thresh).astype(int))
        
    metric_overall['sent_auc'] = auc
    metric_overall['sent_prc'] = prc   
    metric_overall['sent_p'] = p[-1]
    metric_overall['sent_r'] = r[-1]
    metric_overall['sent_f1'] = f1[-1]
    
    if tagging:
        
        all_df = get_token_df_for_label(token_df,
                                         label = label,
                                         sent_true = sent_true,
                                         sent_pred = sent_pred,
                                         tag_true = tag_true,
                                         tag_pred = tag_pred)
        
        print(f"finish collect token info at {time.time() - start_time :.2f}")
        
        metric_article = pd.DataFrame([])
        
        # # Overall PRC/AUC metrics
        
        bert_metric_df = get_sentence_bert_score(all_df, label, sent_pred, sent_true, wordvectors, 
                            sent_thresh, tag_thresh, syn = syn)
        
        print(f"finish compute BERTScore for each sentence at {time.time() - start_time :.2f}")
        
        for k in [1, 3, 10000]:
            
            suffix = "_"+str(k) if k<10000 else ''
            
            if for_correct_sentences:
                df = df[(df.sent_t == 1) & (df.sent_p >= sent_thresh)]
            
            metrics = tag_metric_at_k(all_df, wv = wordvectors, sent_thresh = sent_thresh, tag_thresh = tag_thresh, k = k)
            if metrics is not None:
                metrics = metrics[["precision", "recall", 'bert_pre','bert_rec']]
                metrics.columns = ['token_p', 'token_r', 'bert_pre','bert_rec']
                metrics.columns = [col + suffix for col in metrics.columns]
                metric_article = pd.concat([metric_article, metrics], axis = 1)

        # auc/prc at article level
        colnames = metric_article.columns.tolist()
        auc_article = all_df.groupby("pmid").apply(lambda d: roc_auc_score(d.tag_t, d.tag_p) if d.tag_t.nunique()>1 else None)
        metric_article = pd.concat([metric_article, auc_article], axis = 1) 
        prc_article = all_df.groupby("pmid").apply(lambda d: average_precision_score(d.tag_t, d.tag_p) if d.tag_t.nunique()>1 else None)
        metric_article = pd.concat([metric_article, prc_article], axis = 1) 
        metric_article.columns  = colnames + ['auc','prc']
        
        auc = roc_auc_score(all_df.tag_t, all_df.tag_p)
        prc = average_precision_score(all_df.tag_t, all_df.tag_p)  
        
        pred_binary = (all_df.sent_p >= sent_thresh).astype(int) * (all_df.tag_p >= tag_thresh).astype(int) 
        p,r, f1,_ = precision_recall_fscore_support(all_df.tag_t, pred_binary)
        
        metric_overall['tag_auc'] = auc
        metric_overall['tag_prc'] = prc
        metric_overall['tag_p'] = p[-1]
        metric_overall['tag_r'] = r[-1]
        metric_overall['tag_f1'] = f1[-1]
            
        metric_article = metric_article.reset_index()
    
    print(f"finish compute metrics for class {label} at {time.time() - start_time :.2f}")
    
    return metrics_classifier,  metric_article, metric_overall, bert_metric_df, all_df

# Evaluate a model
def evaluate_a_model(model_name, 
                     thresh_dict,
                     sent_thresh_dict = None,
                     topk = 3,
                     tagging_perf = True,  # whether calculate tagging performance
                     for_correct_sentences = False,
                     remove_punct = True, 
                     remove_stop = True, 
                     stop_words = stopwords.words('english'),
                     base_data_folder = "../data",             # base folder where test data exists
                     base_result_folder = "../result",
                     labels = ['participants', 'interventions','outcomes'],
                     pred_labels = ['participants_pred', 'interventions_pred','outcomes_pred']
                     ):

    np.set_printoptions(precision=4)

    # load test data
    df_expert = pd.read_csv(os.path.join(base_data_folder, 'test_sentence_expert.csv'))
    df_expert[labels] = df_expert[labels].fillna(0)
    len(df_expert)
    
    df_pred = pd.read_csv(os.path.join(base_result_folder, model_name, 'sentence_pred.csv'))
    print(f"prediction results loaded from {os.path.join(base_result_folder, model_name, 'sentence_pred.csv')}")

    if tagging_perf:
        wv = np.load(os.path.join(base_data_folder,'wordvectors.npy'))
        mask = np.load(os.path.join(base_data_folder,'sentence_masks.npy'))

        alignment = pickle.load(open(os.path.join(base_data_folder,"alignment.pkl"),"rb"))

        true_tag = pickle.load(open(os.path.join(base_data_folder,"frag_token_ids.pkl"),"rb"))
        
        pred_tag = pickle.load(open(os.path.join(base_result_folder, model_name, "tag_pred.pkl"),"rb"))
        
    else:
        wv = None

        alignment = None
        true_tag = None
        pred_tag = None


    print("\n\n")
    print(f"=============={model_name}==============")


    classify_result = pd.DataFrame([])
    tag_result_sent = pd.DataFrame([])
    tag_result_article = pd.DataFrame([])
    overall_result = {}

    # set label values to the predicted ones for tagging performance
    df_pred[labels] = df_pred[pred_labels]
    
    #print(df_pred[labels].head())
    #print( df_expert[labels].head())
    
    if tagging_perf:
        token_df = get_token_df(alignment, 
                            remove_stop = remove_stop, 
                            stop_words = stop_words,
                            remove_punct = remove_punct)
    else:
        token_df = None
    
    for label in labels:

        metrics_classifier,  metric_article, metric_overall, metric_sent, all_df = classify_tag_metrics(label,
                        df_expert, df_pred, 
                        token_df = token_df,
                        tag_true = true_tag, 
                        tag_pred = pred_tag,
                        #att_tag = att_tag, 
                        wordvectors = wv,  
                        topk = topk,
                        sent_thresh = sent_thresh_dict[label], tag_thresh = thresh_dict[label],
                        syn = True, tagging = tagging_perf,
                        for_correct_sentences = for_correct_sentences)
        
        metrics_classifier['label'] = label
        classify_result = pd.concat([classify_result, metrics_classifier], axis = 0, ignore_index= True)
        
        overall_result[label] = metric_overall

        if tagging_perf:
            metric_sent['label'] = label
            tag_result_sent = pd.concat([tag_result_sent, metric_sent], axis = 0, ignore_index= True)
            
            metric_article['label'] = label
            tag_result_article = pd.concat([tag_result_article, metric_article], axis = 0, ignore_index= True)

    if for_correct_sentences:
        article_save_file = "tag_metric_article_correct_only.csv"
        sent_save_file = "tag_metric_sent_correct_only.csv"
        overall_save_file = "tag_metric_overall_correct_only.csv"
        classify_save_file = "classify_metrics_correct_only.csv"
    else:
        article_save_file = "tag_metric_article.csv"
        sent_save_file = "tag_metric_sent.csv"
        overall_save_file = "tag_metric_overall.csv"
        classify_save_file = "classify_metrics.csv"
        
    if tagging_perf:
        
        tag_result_article.to_csv(os.path.join(base_result_folder, model_name, article_save_file), 
                                header = True, index = False)
        
        tag_result_sent.to_csv(os.path.join(base_result_folder, model_name, sent_save_file), 
                                header = True, index = False)
        
    overall_result = pd.DataFrame.from_dict(overall_result, orient = 'index')
    cols = overall_result.columns.tolist()
    overall_result = overall_result.reset_index()
    overall_result.columns = ['label'] + cols
    overall_result.to_csv(os.path.join(base_result_folder, model_name, overall_save_file), index = False)

    classify_result.to_csv(os.path.join(base_result_folder, model_name, classify_save_file), index = False)
    
    return classify_result, tag_result_sent, tag_result_article, overall_result
        

# Utility function to clean up text
def is_caption(s, threshold = 0.6):
    
    s = s.strip()
    word_in_s = re.findall(r'[a-zA-Z][a-zA-Z]+', unidecode(s), re.UNICODE)
    result = False

    if len(word_in_s)>= 5 :  # minimal 5 words in a sentence
        # sometimes, a number or a,b, ... may preceds a word, remove the number
        if len(re.findall(r"\b[a-z\d]?[A-Z][a-zA-Z]+", unidecode(s), re.UNICODE))/len(word_in_s) >= threshold:
            result = True
    else:
        result = True    # filter sentences with less than 5 words
            
    return result

# topk predictions from all models are saved into subset_df so that all models predict the same subset
def get_subset_preds(file_id, subset_df, 
                   pred_folder = "../WD/result/full", 
                   #true_tag_file = "../WD/test/tag_truth.xlsx",
                   truth_folder = '../../FSR/data/test_biobert_vectors', 
                   tagging = True,
                   labels = ["Study Period",	"Perspective",	"Population",	"Sample Size",	"Intervention", "Country"]):
    
    #read sentence predicts
    sent_pred = pd.read_csv(os.path.join(pred_folder, file_id+".csv"))
    # fix sid issue
    if 'sid' not in sent_pred.columns:
        sent_pred.columns = ['sid'] + sent_pred.columns.tolist()[1:]
    
     # read true tags
    test_pack = pickle.load(open(os.path.join(truth_folder, file_id + ".pkl"),'rb'))
    
    selected_idx = sent_pred[sent_pred.sid.isin(subset_df[subset_df.pmid == file_id].sid.values)]
    selected_idx = selected_idx.index.values
    
    sent_pred_out = sent_pred.loc[selected_idx][["sid","sent"] +labels].copy()
    sent_pred_out["pmid"] = file_id

    alignment_out = [test_pack['tokened_sentences'][i] for i in selected_idx]
    wv = test_pack['wordvector'][selected_idx]
    mask = test_pack['mask'][selected_idx]
    
    # read tag predicts
    tag_pred = None
    tag_att = None
    
    tag_att_out = None
    tag_pred_out = None
    tag_true_out = None
    sent_true_out = sent_pred_out.copy()
    sent_true_out[labels] = 0
    
    if tagging:
        tag_pred_out = {}
        tag_true_out = {}
        tag_pred = pickle.load(open(os.path.join(pred_folder, file_id + "_tag.pkl"),'rb'))
        
    for label in labels:
        
        if tagging:
            tag_pred_out[label] = tag_pred[label][selected_idx]
            # true tag
            tag_true_out[label] = 0 * test_pack['mask'][selected_idx]
    
        # update sent_true and tag_true
        if label in test_pack['tags']:
                
            true_idx = list(test_pack['tags'][label].keys())
            
            for idx in true_idx:
                if idx in selected_idx:
                    i = (list(selected_idx)).index(idx)
                    # update sentence truth
                    sent_true_out.loc[idx,label] = 1
                    
                    # update tag truth
                    if tagging:
                        true_tag_ids = test_pack['tags'][label][idx]
                        #print(f"{i}, {label}: {true_tag_ids}")
                        tag_true_out[label][i][true_tag_ids] = 1
    
    # read tag attention
    if os.path.exists(os.path.join(pred_folder, file_id + "_att.pkl")):
        tag_att = pickle.load(open(os.path.join(pred_folder, file_id + "_att.pkl"),'rb'))
        tag_att_out = {}
        for label in labels:
            tag_att_out[label] = tag_att[label][selected_idx]
    
    output = {"sent_pred": sent_pred_out,
              "tag_pred": tag_pred_out ,
              "tag_att": tag_att_out if tagging else None,
              "sent_true": sent_true_out,
              "tag_true": tag_true_out if tagging else None,
              "alignment": alignment_out if tagging else None,
              'wordvector': wv if tagging else None,
              'mask': mask if tagging else None}
    
    return output


# Get topK sentences if an article has many sentences. For WD case
def get_topk_preds(file_id, topk = 5, 
                   pred_folder = "../WD/result/full", 
                   #true_tag_file = "../WD/test/tag_truth.xlsx",
                   truth_folder = '../../FSR/data/test_biobert_vectors', 
                   tagging = True,
                   labels = ["Study Period",	"Perspective",	"Population",	"Sample Size",	"Intervention", "Country"]):
    
    #read sentence predicts
    sent_pred = pd.read_csv(os.path.join(pred_folder, file_id+".csv"))
    # fix sid issue
    if 'sid' not in sent_pred.columns:
        sent_pred.columns = ['sid'] + sent_pred.columns.tolist()[1:]
    
    # read tag predicts
    tag_pred = None
    tag_att = None
    if tagging:
        tag_pred = pickle.load(open(os.path.join(pred_folder, file_id + "_tag.pkl"),'rb'))
         # read tag attention
        if os.path.exists(os.path.join(pred_folder, file_id + "_att.pkl")):
            tag_att = pickle.load(open(os.path.join(pred_folder, file_id + "_att.pkl"),'rb'))
    
    # read true tags
    test_pack = pickle.load(open(os.path.join(truth_folder, file_id + ".pkl"),'rb'))
    
    # only the union of topk sentences and true sentences are selected for performance calculation
    selected_idx = []
    
    for label in labels:
        
         # filter out address sentences for country
        #if label == 'Country':
        is_address = sent_pred["sent"].apply(lambda s: is_caption(s, threshold = 0.7))
        sent_pred.loc[is_address, label] = 0
            
        #true_tag = pd.read_excel(true_tag_file, sheet_name=label)
        #true_tag["file_id"] = true_tag["file_id"].astype(int).astype(str)
        
        # top k sentences
        sent_pred["rank"] = sent_pred[label].rank(method="dense", ascending=False) 
        topk_idx = sent_pred[sent_pred["rank"]<=topk].index.tolist()
        selected_idx = selected_idx + topk_idx
        
        # true sentence
        if label in test_pack['tags']:
            true_idx = list(test_pack['tags'][label].keys())
            #true_idx = true_tag[(true_tag["label"] == 1) & (true_tag["file_id"] == str(file_id))].sid.tolist()
            selected_idx = selected_idx + true_idx
            #print(f"file id: {file_id}, true sents: {len(true_idx)}")
        
    
    # get selected sent_pred, sent_true, tag_pred, tag_true
    selected_idx = sorted(list(set(selected_idx)))
    
    # selected sent_pred out
    sent_pred_out = sent_pred.loc[selected_idx][["sid","sent"] +labels].copy()
    #sent_pred_out = sent_pred[sent_pred.sid.isin(selected_idx)][["sid","sent"] +labels].copy()
    sent_pred_out["pmid"] = file_id
    
    alignment_out = [test_pack['tokened_sentences'][i] for i in selected_idx]
    wv = test_pack['wordvector'][selected_idx]
    mask = test_pack['mask'][selected_idx]
    
    tag_pred_out = {}
    tag_att_out = {}
    tag_true_out = {}
    
    sent_true_out = sent_pred.loc[selected_idx][["sid","sent"] +labels].copy()
    sent_true_out[labels] = 0
    sent_true_out["pmid"] = file_id
    
    # selected sent_true out
    for label in labels:

        tag_true_out[label] = 0 * test_pack['mask'][selected_idx]
        
        # update sent_true and tag_true
        if label in test_pack['tags']:
            true_idx = list(test_pack['tags'][label].keys())
            sent_true_out.loc[true_idx, label] = 1
            
            #print(f"{label}: {true_idx}")
            for idx in true_idx:
                i = selected_idx.index(idx)
                true_tag_ids = test_pack['tags'][label][idx]
                #print(f"{i}, {label}: {true_tag_ids}")
                tag_true_out[label][i][true_tag_ids] = 1
    
        # selected tag_pred out
        
        if tag_pred is not None:
            tag_pred_out[label] = tag_pred[label][selected_idx]
            
        if tag_att is not None:
            tag_att_out[label] = tag_att[label][selected_idx]
    
    output = {"sent_pred": sent_pred_out,
              "tag_pred": tag_pred_out if tagging else None,
              "tag_att": tag_att_out if len(tag_att_out)<0 else None,
              "sent_true": sent_true_out,
              "tag_true": tag_true_out if tagging else None,
              "alignment": alignment_out if tagging else None,
              'wordvector': wv if tagging else None,
              'mask': mask if tagging else None}
    
    return output


# For WD case
def prepare_classify_tag_output(file_id,  
                   pred_folder = "../WD/result/full", 
                   #true_tag_file = "../WD/test/tag_truth.xlsx",
                   truth_folder = '../../FSR/data/test_biobert_vectors', 
                   tagging = True,
                   labels = ["Study Period",	"Perspective",	"Population",	"Sample Size",	"Intervention", "Country"]):
    
    #read sentence predicts
    sent_pred = pd.read_csv(os.path.join(pred_folder, file_id+".csv"))
    # fix sid issue
    if 'sid' not in sent_pred.columns:
        sent_pred.columns = ['sid'] + sent_pred.columns.tolist()[1:]
    
    # read tag predicts
    tag_pred = None
    tag_att = None
    if tagging:
        tag_pred = pickle.load(open(os.path.join(pred_folder, file_id + "_tag.pkl"),'rb'))
    
        # read tag attention
        if os.path.exists(os.path.join(pred_folder, file_id + "_att.pkl")):
            tag_att = pickle.load(open(os.path.join(pred_folder, file_id + "_att.pkl"),'rb'))
            #print(f"tag att: {len(tag_att['Perspective'])}")
    
    # read true tags
    test_pack = pickle.load(open(os.path.join(truth_folder, file_id + ".pkl"),'rb'))
    
    sent_pred["pmid"] = file_id
    
    sids = sent_pred.sid.tolist()
    alignment = [test_pack['tokened_sentences'][i] for i in sids]
    wv = test_pack['wordvector'][sids]
    mask = test_pack['mask'][sids]
    
    sent_true = sent_pred.copy()
    sent_true[labels] = 0
    tag_true = {}
    #start_time = time.time()
    
    # selected sent_true out
    for label in labels:
        
        # filter out address sentences for country
        if label == 'Country':
            is_address = sent_pred["sent"].apply(lambda s: is_caption(s, threshold = 0.7))
            sent_pred.loc[is_address, label] = 0
        
        #print(f"{label} @ {time.time()-start_time}")
        
        tag_true[label] = 0 * mask
        
        # update sent_true and tag_true
        if label in test_pack['tags']:
            true_idx = list(test_pack['tags'][label].keys())
            sent_true.loc[sent_true.sid.isin(true_idx), label] = 1
            
            #print(f"{label}: {true_idx}")
            for idx in true_idx:
                if idx in sids:
                    i = sids.index(idx)
                    true_tag_ids = test_pack['tags'][label][idx]
                    #print(f"{i}, {label}: {true_tag_ids}")
                    tag_true[label][i][true_tag_ids] = 1
    
    
    output = {"sent_pred": sent_pred,
              "tag_pred": tag_pred if tagging else None,
              "tag_att": tag_att,
              "sent_true": sent_true,
              "tag_true": tag_true if tagging else None,
              "alignment": alignment if tagging else None,
              'wordvector': wv if tagging else None,
              'mask': mask if tagging else None}
    
    return output


def aggregate_WD_preds(pred_folder = "../WD/pred/full", 
                        truth_folder = '../../FSR/data/test_biobert_vectors', 
                        result_folder = "../WD/result/full",
                        topk_pred_only = False,
                        topk_subset = None,       # a datafram with pmid, sid, and sent columns
                        topk = 5,
                        tagging = True,
                       labels = ["Study Period",	"Perspective",	"Population",	"Sample Size",	"Intervention", "Country"]):

    sent_pred = pd.DataFrame([])
    tag_pred = {label: [] for label in labels}
    tag_att = {label: [] for label in labels}
    sent_true = pd.DataFrame([])
    tag_true = {label: [] for label in labels}
    alignment = []
    wv = []
    mask = []
    
    if not os.path.exists(result_folder):
      os.makedirs(result_folder, exist_ok = True)
            
    start_time = time.time()
    cnt = 0
    for file_name in glob.glob(os.path.join(pred_folder, "*.csv")):
        
        cnt += 1
        file_id = (file_name.split("/")[-1]).split(".")[0]
        
        if not os.path.exists(os.path.join(truth_folder, file_id + ".pkl")):
            continue
        
        if topk_subset is not None:
            output = get_subset_preds(file_id = file_id, 
                                subset_df = topk_subset, 
                                #true_tag_file = true_tag_file,
                                pred_folder = pred_folder,
                                truth_folder = truth_folder, 
                                tagging = tagging,
                                labels = labels)
        elif topk_pred_only:
            
            output = prepare_classify_tag_output(file_id = file_id,
                                pred_folder = pred_folder,
                                truth_folder = truth_folder, 
                                tagging = tagging,
                                labels = labels)
        else:
            output = get_topk_preds(file_id = file_id, 
                                topk = topk, 
                                #true_tag_file = true_tag_file,
                                pred_folder = pred_folder,
                                truth_folder = truth_folder, 
                                tagging = tagging,
                                labels = labels)
        
        sent_pred = pd.concat([sent_pred, output["sent_pred"]], axis = 0, ignore_index = True)
        sent_true = pd.concat([sent_true, output["sent_true"]], axis = 0, ignore_index = True)
        #print(f"{cnt}: file_id: {file_id}: {file_name}, pred: {len(sent_pred)}, true: {len(sent_true)} @ {time.time() - start_time :.2f}")
        
        if tagging:
            for label in labels:
                tag_pred[label].append(output["tag_pred"][label])
                tag_true[label].append(output["tag_true"][label])
                if output["tag_att"] is not None:   
                    tag_att[label].append(output["tag_att"][label])
                else:
                    tag_att = None
            
            alignment = alignment + output["alignment"]
            wv.append(output['wordvector'])
            mask.append (output['mask'])

    if tagging:
        for label in labels:
            tag_pred[label] = np.concatenate(tag_pred[label], axis = 0)
            tag_true[label] = np.concatenate(tag_true[label], axis = 0)
            if tag_att is not None:
                tag_att[label] = np.concatenate(tag_att[label], axis = 0)
                
        wv = np.concatenate(wv, axis = 0)    
        mask = np.concatenate(mask, axis = 0)
        
    # some model use logits. convert to prob.
    for label in labels:
        if sent_pred[label].min()<-0.1:
            sent_pred[label] = 1/(1+np.exp(-sent_pred[label].values))
        
    output = {"sent_pred": sent_pred,
                "tag_pred": tag_pred if tagging else None,
                "tag_att": tag_att,
                "sent_true": sent_true,
                "tag_true": tag_true if tagging else None,
                "alignment": alignment if tagging else None,
                "tag_att": tag_att if tagging else None,
                'wordvector': wv if tagging else None,
                'mask': mask if tagging else None}

    #print(output["sent_pred"].head())
    pickle.dump(output, open(os.path.join(result_folder, 'all_outputs.pkl'), 'wb'))
    
    return output


# Get WD model performance
def get_WD_model_perf(model_name,
                      thresh_dict = None,
                     sent_thresh_dict = None,
                      result_folder = "../WD/result",
                      pred_folder = "../WD/pred", 
                      truth_folder = '../../FSR/data/test_biobert_vectors', 
                      topk_pred_only = False,    
                      topk_subset = False,       # a datafram with pmid, sid, and sent columns                
                      topk = 5,       # if not topk_pred_only, set topk to reduce processing time
                      tagging_perf = True,
                      for_correct_sentences = False,
                      labels = ["Study Period",	"Perspective",	"Population",	"Sample Size",	"Intervention", "Country"]):
    
    # refresh truth since it's updated
    output = aggregate_WD_preds(pred_folder = os.path.join(pred_folder, model_name), 
                                     truth_folder = truth_folder, 
                                     result_folder = os.path.join(result_folder, model_name),
                                     topk_pred_only = topk_pred_only,
                                     topk_subset = topk_subset,       # a datafram with pmid, sid, and sent columns
                                     topk = 5,
                                     tagging = tagging_perf,
                                     labels = labels)
    
    print(f"The number of sentences: {len(output['sent_pred'])}")
        
    classify_result = pd.DataFrame([])
    tag_result_sent = pd.DataFrame([])
    tag_result_article = pd.DataFrame([])
    overall_result = {}

    remove_punct = True 
    remove_stop = True 
    stop_words = stopwords.words('english')
    if sent_thresh_dict is None:
        sent_thresh_dict = {label: 0.5 for label in labels}
    
    if thresh_dict is None:    
        thresh_dict = {label: 0.5 for label in labels}
    
    if tagging_perf:
        token_df = get_token_df(output["alignment"], 
                            remove_stop = remove_stop, 
                            stop_words = stop_words,
                            remove_punct = remove_punct)
    else:
        token_df = None

    for label in labels:

        print(f"==========={label}==========")
            
        metrics_classifier,  metric_article, metric_overall, metric_sent, _ = classify_tag_metrics(label,
                        sent_true = output["sent_true"],
                        sent_pred = output["sent_pred"],
                        token_df = token_df,
                        tag_true = output["tag_true"],
                        tag_pred = output["tag_pred"],
                        #alignment = output["alignment"],
                        wordvectors = output["wordvector"], 
                        att_tag = output["tag_att"],
                        #att_tag = output["tag_att"], 
                        tag_thresh = thresh_dict[label],
                        sent_thresh = sent_thresh_dict[label],
                        syn = True, tagging = tagging_perf,
                        for_correct_sentences = for_correct_sentences)
        
        metrics_classifier['label'] = label
        classify_result = pd.concat([classify_result, metrics_classifier], axis = 0, ignore_index= True)
        
        overall_result[label] = metric_overall
        #print(overall_result)
        

        if tagging_perf:
            metric_sent['label'] = label
            tag_result_sent = pd.concat([tag_result_sent, metric_sent], axis = 0, ignore_index= True)
            
            metric_article['label'] = label
            tag_result_article = pd.concat([tag_result_article, metric_article], axis = 0, ignore_index= True)
        else:
            sent_true = output["sent_true"]
            sent_pred = output["sent_pred"]
            
            metric_sent = sent_pred[["pmid","sid",label]].copy()
            metric_sent = metric_sent.rename({label: "sent_p"}, axis = 1)
            
            metric_sent = sent_true[["pmid","sid",label]].merge(metric_sent[["pmid","sid","sent_p"]], on = ["pmid","sid"])
            metric_sent = metric_sent[["pmid","sid",label,"sent_p"]]
            metric_sent.columns = ["pmid","sid","sent_t","sent_p"]
            metric_sent['label'] = label
            
            tag_result_sent = pd.concat([tag_result_sent, metric_sent], axis = 0, ignore_index= True)

    if for_correct_sentences:
        article_save_file = "tag_metric_article_correct_only.csv"
        sent_save_file = "tag_metric_sent_correct_only.csv"
        overall_save_file = "tag_metric_overall_correct_only.csv"
        classify_save_file = "classify_metrics_correct_only.csv"
    else:
        article_save_file = "tag_metric_article.csv"
        sent_save_file = "tag_metric_sent.csv"
        overall_save_file = "tag_metric_overall.csv"
        classify_save_file = "classify_metrics.csv"
        
    if tagging_perf:
            
        tag_result_article.to_csv(os.path.join(result_folder, model_name, article_save_file), 
                                header = True, index = False)
        
    tag_result_sent.to_csv(os.path.join(result_folder, model_name, sent_save_file), 
                                header = True, index = False)
        
    overall_result = pd.DataFrame.from_dict(overall_result, orient = 'index')
    #print(overall_result)
    cols = overall_result.columns.tolist()
    overall_result = overall_result.reset_index()
    overall_result.columns = ['label'] + cols
    overall_result.to_csv(os.path.join(result_folder, model_name, overall_save_file), index = False)

    classify_result.to_csv(os.path.join(result_folder, model_name, classify_save_file), index = False)
    
    return classify_result, tag_result_sent, tag_result_article, overall_result


def compute_f1(df, p_cols, r_cols, f1_cols):
    for p, r, f1 in zip(p_cols, r_cols, f1_cols):
        df[f1] = 2*df[p]*df[r]/(df[p]+df[r] + 1e-7)
    return df



## Function to retrieve token_df so that statistical comparison for F1 and PRC can be done

def get_all_WD_dfs(model_name,
                      thresh_dict = None,
                     sent_thresh_dict = None,
                      result_folder = "../WD/result",
                      pred_folder = "../WD/pred", 
                      truth_folder = '../../FSR/data/test_biobert_vectors', 
                      topk_pred_only = False,    
                      topk_subset = False,       # a datafram with pmid, sid, and sent columns                
                      topk = 5,       # if not topk_pred_only, set topk to reduce processing time
                      tagging = True,
                      for_correct_sentences = False,
                      labels = ["Study Period",	"Perspective",	"Population",	"Sample Size",	"Intervention", "Country"]):

    df_dict ={}
   
    output = aggregate_WD_preds(pred_folder = os.path.join(pred_folder, model_name), 
                                     truth_folder = truth_folder, 
                                     result_folder = os.path.join(result_folder, model_name),
                                     topk_pred_only = topk_pred_only,
                                     topk_subset = topk_subset,       # a datafram with pmid, sid, and sent columns
                                     topk = 5,
                                     tagging = tagging,
                                     labels = labels)
    
    print(f"The number of sentences: {len(output['sent_pred'])}")
        
    df_dict["sent_true"] = output["sent_true"]
    df_dict["sent_pred"] = output["sent_pred"]

    remove_punct = True 
    remove_stop = True 
    stop_words = stopwords.words('english')
    if sent_thresh_dict is None:
        sent_thresh_dict = {label: 0.5 for label in labels}
    
    if thresh_dict is None:    
        thresh_dict = {label: 0.5 for label in labels}
    
    if tagging:
        token_df = get_token_df(output["alignment"], 
                            remove_stop = remove_stop, 
                            stop_words = stop_words,
                            remove_punct = remove_punct)
    else:
        token_df = None
        
    if tagging:
        
        df_dict["tag"] = {}
        
        for label in labels:

            sent_pred = output["sent_pred"]
            sent_pred["rank"] = sent_pred.groupby("pmid")[label].rank(method="first", ascending=False)
            all_df = get_token_df_for_label(token_df,
                                         label = label,
                                         sent_true = output["sent_true"],
                                         sent_pred = sent_pred,
                                         tag_true = output["tag_true"],
                                         tag_pred = output["tag_pred"])

            df_dict["tag"][label] = all_df
    
    return df_dict
            

# function to report final performance
def report_performance(result_path):
    
    # classifying metrics
    classify_metrics = pd.read_csv(os.path.join(result_path, "classify_metrics.csv"))
    classify_metrics = classify_metrics.groupby("label").mean()
    p_cols = ['p_1','p_3','p']
    r_cols = ['r_1','r_3','r']
    f1_cols = ['f1_1','f1_3','f1']
    classify_metrics = compute_f1(classify_metrics, p_cols, r_cols, f1_cols)

    # tagging metrics
    tag_metrics = pd.read_csv(os.path.join(result_path, "tag_metric_article.csv"))
    tag_metrics = tag_metrics.groupby("label").mean()
    p_cols = ['token_p_1','token_p_3','token_p','bert_pre_1','bert_pre_3','bert_pre']
    r_cols = ['token_r_1','token_r_3','token_r','bert_rec_1','bert_rec_3','bert_rec']
    f1_cols = ['token_f1_1','token_f1_3','token_f1', 'bert_f1_1','bert_f1_3','bert_f1']
    tag_metrics = compute_f1(tag_metrics, p_cols, r_cols, f1_cols)

    # overall performance metrics, e.g., AUC, PRC
    overall_metrics = pd.read_csv(os.path.join(result_path, "tag_metric_overall.csv"))
    overall_metrics = overall_metrics.set_index("label")

    # reorganize into classification and tagging metrics
    sent_cols = [col for col in overall_metrics.columns if 'sent_' in col]
    tag_cols = [col for col in overall_metrics.columns if 'tag_' in col]

    # report final performance on paper
    classifying = pd.concat([classify_metrics, overall_metrics[sent_cols]], axis = 1)
    classifying = classifying[['p_3', 'r_3', 'f1_3', 'sent_prc']]
    
    tagging = pd.concat([tag_metrics, overall_metrics[tag_cols]], axis = 1)
    tagging  = tagging[['token_p_3','token_r_3', 'token_f1_3', 'bert_pre_3', 'bert_rec_3', 'bert_f1_3', 'prc']]
    
    return classifying, tagging
