
import os
import time
import pandas as pd
import torch
from  nltk.corpus import stopwords
import time
import json
import sys
import train_model as tm
import perf_eval as v

pd.options.display.float_format = '{:,.4f}'.format

# If there's a GPU available...
if torch.cuda.is_available():    
  
    device = torch.device("cuda")
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(0))

else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")

# read config json file from command line
config_file = sys.argv[1]

if not os.path.exists(config_file):
    print("Configuration file {config_file} does not exist!")
    sys.exit("Provide a valid configuration json file")

exec_config = json.load(open(config_file,'r'))

# Set up folders
# dataset, result, and model folders should have the same number of elements
# Need to have more sanity check here
if 'run_config' in exec_config:
    
    # training data folders
    data_folders = exec_config['run_config']['data_folders']
    
    # folders to save prediction results
    result_folders = exec_config['run_config']['result_folders']
    
    # folders to save model
    model_folders = exec_config['run_config']['model_folders']
    # folder for test data 
    test_data_folder = exec_config['run_config']['test_data_folder']
    # test sentence csv file
    test_text_file = exec_config['run_config']['test_text_file']
    
if 'model_config' in exec_config:
    config = exec_config["model_config"]


model_name = exec_config['name']
for_ablation = exec_config['ablation']

for data_folder, result_folder, model_folder in zip(data_folders, result_folders, model_folders):

    print(f"=========== {model_name} ==============")

    # ## Train
    start_time = time.time()
    
    # start training
    tm.train(model_path = os.path.join(model_folder, model_name), 
                device = device,
                #use_context = False, 
                #use_fragment = True,
                config = config,
                train_data_path = data_folder,
                ablation = for_ablation)
    
    print(f"Completed training {model_name} in {time.time() - start_time :.2f}")
    

    tm.test_sentences(model_path = os.path.join(model_folder, model_name), 
                        result_path = os.path.join(result_folder, model_name), 
                        device = device,
                        batch = 2,
                        config = config,
                        text_file = test_text_file,   # test sentence file
                        test_data_path = test_data_folder,                        # test data folder
                        train_data_path = data_folder,
                        ablation = for_ablation
                        )
    print(f"Completed test {model_name} in {time.time() - start_time :.2f}")

    # evaluate a model
    # Tagging threshold dictionary
    thresh_dict = {'participants': 0.5, 'interventions':0.5,'outcomes': 0.5}
    # Sentence threshold dictionary
    sent_thresh_dict ={'participants': 0.5, 'interventions':0.5,'outcomes': 0.5}

    classify_result, tag_result_sent, tag_result_article, overall_result = v.evaluate_a_model(model_name, 
                        thresh_dict,
                        sent_thresh_dict = sent_thresh_dict,
                        topk = 3,
                        tagging_perf = True,
                        remove_punct = True, 
                        remove_stop = True, 
                        stop_words = stopwords.words('english'),
                        base_data_folder = test_data_folder,            # location to load ground truth file
                        base_result_folder = result_folder)


    print(overall_result)
   

