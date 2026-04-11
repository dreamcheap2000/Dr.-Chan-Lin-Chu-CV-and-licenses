
from data_batch import Data_loader
from model import Text_Encoder, FastSR,  Attention, Context_Attention
from model_ablation import FastSR_Ablation
from config import ModelConfig
import os
import glob
import time
import pickle
import numpy as np
from sklearn.metrics import classification_report, precision_recall_fscore_support
import pandas as pd
import torch
from typing import Union, List, Any, Dict

import warnings
from sklearn.exceptions import UndefinedMetricWarning
warnings.filterwarnings(action='ignore', category=UndefinedMetricWarning)

pd.set_option("display.precision", 4)

# train function - single class
def train_a_class(the_model,    # model
                  args,          # model configuration
                  train_loader,       # training data loader
                  valid_loader,       # test dataloader
                  the_device = torch.device("cpu"),
                  model_path: str = '.', 
                  model_name: str = 'model.pth'):

  print(the_model)
  print(the_model.encoder)
    
  if args.use_fragment:
    print(the_model.frag_encoder)

  # track metric for early stopping
  best_metric = 0
  cnt = 0


  the_model = the_model.to(the_device)

  # history
  history = {'train_acc': [], 'train_loss': [],
             'train_acc_avg': [], 'train_loss_avg': [],
             'valid_acc': [], 'valid_loss': [],
             'valid_acc_avg': [], 'valid_loss_avg': [],
             'valid_tag_loss': [], 'valid_tag_metric': []}

  # set up optimizer 
  optimizer = torch.optim.Adam(the_model.parameters(), lr=args.learning_rate)
  
  # dynmaic learning rate
  if args.learning_rate_schedule is True:
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer=optimizer,
                                                          mode = 'min',
                                                          factor = args.gamma,
                                                          patience = 1)
    if args.verbose:
      print(f"Initial learning rate: {optimizer.state_dict()['param_groups'][0]['lr']}")

  for i in range(args.epochs):
    # train metrics
    train_cumulative_acc = 0
    train_cumulative_loss = 0


    for j in range(args.training_eposides):
        
      the_model.train()
      # retrieve data from train loader
      cur_x_support, cur_x_query, cur_y_query = next(train_loader)

      # cur_x_support  and cur_x_query are list of [sem, syntax, context] 
      cur_x_support = {key: cur_x_support[key].to(the_device) for key in cur_x_support} 
      cur_x_query = {key: cur_x_query[key].to(the_device) for key in cur_x_query}
      cur_y_query = cur_y_query.to(the_device)

      model_outputs = the_model(cur_x_support, cur_x_query, cur_y_query, return_loss = True)
      p_y = model_outputs["y_hat"]
      cur_loss =  model_outputs["loss"]
      
      # backward
      cur_loss.backward()

      optimizer.step()
      optimizer.zero_grad()

      # cumulate loss and acc
      p_y = p_y.detach().cpu().numpy()
      y_hat = p_y.argmax(axis = -1)
      cur_acc = (cur_y_query.cpu().numpy().reshape(-1) == y_hat).astype(int).mean()

      train_cumulative_acc += cur_acc
      train_cumulative_loss += cur_loss.item()
      
      # record
      history['train_acc'].append(cur_acc)
      history['train_loss'].append(cur_loss.item())

    # evaluation metrics
    valid_cumulative_loss = 0
    valid_cumulative_tag_loss = 0

    valid_pred = []
    valid_label = []
    
    actual_tags = []
    predict_tags = []
    
    valid_tag_metric = {}
    
    for k in range(args.validation_eposides):
      the_model.eval()
      # retrieve data from validation loader
      data_batch = next(valid_loader)

      cur_x_support = {key: data_batch[0][key].to(the_device) for key in data_batch[0]} 
      cur_x_query = {key: data_batch[1][key].to(the_device) for key in data_batch[1]}
      cur_y_query = data_batch[2].to(the_device)

      # evaluation

      with torch.no_grad():
        model_outputs = the_model(cur_x_support, cur_x_query, cur_y_query, \
                                  return_loss = True, return_tag = args.tagging )
      
      p_y = model_outputs["y_hat"]
      loss =  model_outputs["loss"]
    
      p_y = p_y.detach().cpu().numpy()
      y_hat = p_y.argmax(axis = -1)

      # metrics
      valid_pred.append(y_hat)
      valid_label.append(data_batch[2].cpu().numpy())
      #valid_cumulative_acc += acc
      valid_cumulative_loss += loss.item()
        
      if args.tagging:
          predicted_tags = model_outputs["tag"].detach().cpu().numpy()
          #predicted_tags = (predicted_tags>0.5).astype(int)
          predicted_tags = (predicted_tags>0.5).astype(int) * y_hat[:,None]
          actual_labels = model_outputs["tag_label"].detach().cpu().numpy()
          query_mask = model_outputs["query_mask"].detach().cpu().numpy()
          
          predicted_tags = predicted_tags * query_mask
            
          actual_tags.append(actual_labels)
          predict_tags.append(predicted_tags)
          
          tag_loss =  model_outputs["tag_loss"]
          valid_cumulative_tag_loss += tag_loss.item()
          
        
    valid_pred = np.concatenate(valid_pred).reshape(-1)
    valid_label = np.concatenate(valid_label).reshape(-1)

    cur_acc = (valid_pred == valid_label).astype(int).mean()
    cur_loss = valid_cumulative_loss / args.validation_eposides

    # learning rate schedule
    if args.learning_rate_schedule is True:
        scheduler.step(cur_loss)

    # calculate precision, recall, and f1
    p,r,f1,_ = precision_recall_fscore_support(y_true=valid_label, y_pred=valid_pred)
        
    # record
    history['train_acc_avg'].append(train_cumulative_acc / args.training_eposides)
    history['train_loss_avg'].append(train_cumulative_loss / args.training_eposides)
    history['valid_acc_avg'].append(cur_acc)
    history['valid_loss_avg'].append(cur_loss)
    
    # Tagging performance
    if args.tagging:
        
        valid_avg_tag_loss = valid_cumulative_tag_loss/args.validation_eposides
        
        actual_tags = np.concatenate(actual_tags, axis = 0).reshape(-1)
        predict_tags = np.concatenate(predict_tags, axis = 0).reshape(-1)
        
        tag_prec, tag_recall, tag_f1, _ = precision_recall_fscore_support(actual_tags, predict_tags)
        
        valid_tag_metric["prec"] = tag_prec
        valid_tag_metric["recall"] = tag_recall
        valid_tag_metric["f1"] = tag_f1
        
        valid_tag_acc = (actual_tags == predict_tags).astype(int).mean()
        valid_tag_metric["acc"] = valid_tag_acc
        
        history['valid_tag_loss'].append(valid_avg_tag_loss)
        history['valid_tag_metric'].append(valid_tag_metric)
        
    
    # verbose
    if args.verbose:
        
      print(f"Component weights: {the_model.component_weights}, tagging weight: {the_model.tag_cost_weight}")
    
      print('=' * 10 + f'Epoch: {i + 1} / {args.epochs}' + '=' * 10)
      print(f'\nTrain acc: {(train_cumulative_acc / args.training_eposides):.4f}, Train loss: {(train_cumulative_loss / args.training_eposides):.4f}')
      print(f'\nValidation acc: {cur_acc:.4f}, Validation loss: {(valid_cumulative_loss / args.validation_eposides):.4f}')
      
      print('\nClassifying:')
      print(classification_report(y_true=valid_label, y_pred=valid_pred))
      print('=' * 37)
        
      if args.tagging:
        print(f'\nValidation tagging loss: {valid_avg_tag_loss:.4f},\
        Validation tagging prec: {valid_tag_metric["prec"].mean():.4f}, \
        recall: {valid_tag_metric["recall"].mean():.4f}, \
        f1: {valid_tag_metric["f1"].mean():.4f}')
        
        print('\n Tagging:')
        print(classification_report(y_true=actual_tags, y_pred=predict_tags))
        print('=' * 37)
        
    print(f"Current learning rate: {optimizer.state_dict()['param_groups'][0]['lr'] :.5f}")

    # tracking tagging loss/f1 if tagging is enabled; otherwise classification loss
    if args.tagging:
       #cur_loss = valid_avg_tag_loss
       cur_f1 = f1[-1] + tag_f1[-1]
    else:
      cur_f1 = f1[-1]
    
    # Early stopping
    if cur_f1 > best_metric:
      best_metric = cur_f1
      #best_loss = cur_loss
      torch.save(the_model.state_dict(), os.path.join(model_path, model_name))

      history["best_prf"] = [p,r,f1]
      history["best_loss"] = cur_loss
      history["best_acc"] = cur_acc
      print(f"classify f1: {f1[-1]:.4f}, loss: {cur_loss:.4f}")

      if args.tagging:
        history["best_tag_prf"] = {key: valid_tag_metric[key] for key in ["prec","recall","f1"]}
        history["best_tag_loss"] = valid_avg_tag_loss
        history["best_tag_acc"] = valid_tag_acc

        print(f"tag f1: {valid_tag_metric['f1'][-1]:.4f}, loss: {valid_avg_tag_loss:.4f}")
      print(f"model saved!")
      print("\n")

      cnt = 0
    else:

      cnt +=1
      if cnt==args.patience:
        print("stop training")
        print("Classification Precision/recall: ", history["best_prf"])
        if args.tagging:
          print("Tagging Precision/recall: ", history["best_tag_prf"])
        print("\n\n")
        break

  return history

# Train all classes
def train_all_classes(args,            # model configuration
                      train_loaders,   # train data loaders
                      valid_loaders,   # validation data loaders
                      the_device = torch.device("cpu"),
                      model_path: str = '.',  # model save path
                      ablation: bool = False  # ablated model 
                      ):

  # retrieve label names; train_loaders is a dictionary of data loaders with label as key
  names = list(train_loaders.keys())

  # build models
  model_list = []
  for _ in range(len(names)):

    if ablation:   # ablation model can separately enable fragment attention
      if args.use_fragment and args.enable_frag_att:
        frag_encoder = Attention(emb_dim = args.emb_dim, 
                                seq_len = args.seq_len,
                                att_projection_layer = args.att_projection_layer,
                                att_hidden_dim = args.att_hidden_dim,
                                value_dim = args.att_value_dim,
                                dropout_rate= args.att_dropout_rate)
      else:
        frag_encoder = None
        
    else:    # full model
      if args.use_fragment:
        frag_encoder = Attention(emb_dim = args.emb_dim, 
                                seq_len = args.seq_len,
                                att_projection_layer = args.att_projection_layer,
                                att_hidden_dim = args.att_hidden_dim,
                                value_dim = args.att_value_dim,
                                dropout_rate= args.att_dropout_rate)
      else:     # Protonet classifier only
        frag_encoder = None

    if args.use_context:
      context_encoder = Context_Attention(emb_dim = args.context_dim, \
                                          context_latent_dim = args.context_latent_dim)
    else:
      context_encoder = None

    encoder = Text_Encoder(emb_dim = args.emb_dim, 
                           seq_len = args.seq_len,
                           num_filters = args.num_filters, 
                           kernel_sizes = args.kernel_sizes,
                           text_projection_layer = args.text_projection_layer,
                           text_hidden_dim = args.text_hidden_dim)
    if ablation:
      cur_model = FastSR_Ablation(args = args, 
                       encoder = encoder, 
                       frag_encoder = frag_encoder, 
                       context_encoder = context_encoder)
    else:
      cur_model = FastSR(args = args, 
                       encoder = encoder, 
                       frag_encoder = frag_encoder, 
                       context_encoder = context_encoder)
      
    model_list.append(cur_model)

  # print models
  print(cur_model)

  if args.use_context:
    print(cur_model.context_encoder)
    

  if args.use_fragment:
    print(cur_model.frag_encoder)

  # train models
  historys = {}
  for i in range(len(names)):
    # extract
    cur_name = names[i]
    cur_model = model_list[i]

    if args.save_model:    

      if not os.path.exists(model_path):
        os.makedirs(model_path)
    
    # train
    if args.verbose:
      print(f'\n\n{cur_name} model training start.\n')

    cur_history = train_a_class(cur_model, args = args,
                              train_loader=train_loaders[cur_name],
                              valid_loader=valid_loaders[cur_name],
                              the_device=the_device,
                              model_path= model_path,
                              model_name = cur_name + '.pth')
    historys[cur_name] = cur_history
    if args.verbose:
      print(f'\n{cur_name} model training finish.\n')
  
  return historys

# Set up dataset and initialize training
def train(model_path: str = ".",            # where to save model
          device = torch.device("cpu"), 
          #use_context: bool = False,        # whether to enable context; change config dynamically
          #use_fragment: bool = False,       # whether to enable context; change config dynamically
          config: Dict = {},                # model additional configurations
          train_data_path: str = '../data/train_bert_emb',  # training data path
          ablation: bool = False
          ):

  args = ModelConfig()
  #args.set_option("use_context", use_context)
  #args.set_option("use_fragment", use_fragment)

  # update model configure parameters
  for key in config:
    args.set_option(key, config[key])

  use_fragment = args.use_fragment
  use_context = args.use_context
  
  feature_path = train_data_path
  model_path = model_path

  print(f"model path: {model_path}, feature path: {feature_path}")
    
  if not os.path.exists(model_path):
    os.makedirs(model_path)

  # only indexes of the sentences are kept in the dictionary
  train_pos_set = pickle.load(open(os.path.join(feature_path, "train_pos_dict.pkl"),"rb"))
  train_neg_set = pickle.load(open(os.path.join(feature_path, "train_neg_dict.pkl"),"rb"))
  val_pos_set = pickle.load(open(os.path.join(feature_path, "val_pos_dict.pkl"),"rb"))
  val_neg_set = pickle.load(open(os.path.join(feature_path, "val_neg_dict.pkl"),"rb"))

  data = {}      # a dictionary to pack all data components needed
  wordvectors = np.load(os.path.join(feature_path, "wordvectors.npy"))
  print(f"word vector size: {wordvectors.shape}")
  
  if args.sentence_mask:
    masks = np.load(os.path.join(feature_path, "sentence_masks.npy"))
    wordvectors = wordvectors * masks[:,:, None]
  else:
    masks = np.all(wordvectors ==0, axis = -1).astype(int)
  
  data["wordvector"] = wordvectors

  emb_dim = wordvectors.shape[-1]
  seq_len = wordvectors.shape[-2]
  args.set_option("emb_dim", emb_dim)
  args.set_option("seq_len", seq_len)

  if use_context:
    section_prob = np.load(os.path.join(feature_path, "section_prob.npy"))
    data["context"] = section_prob
    context_dim = section_prob.shape[-1]
    args.set_option("context_dim", context_dim)
                      
  columns = args.labels

  print("\n======== training argument ===========\n")
  args.print_options()

  # create data loader
  train_loaders = {}
  valid_loaders = {}

  for cur_name in columns:
    #print("use_fragment:", use_fragment)
    
    class_data = {key: data[key].copy() for key in data}    # make a copy for each model since components(e.g., fragment) varies by model
    #print("len of general data: ", len(class_data))
    
    if use_fragment:
      frag_dict = pickle.load(open(os.path.join(feature_path, "frag_token_ids.pkl"), 'rb'))
      
      # mask for fragments in support set
      class_data["fragment"]= frag_dict[cur_name] # num of train sample x sent_length
      
      # masks for query/supports
      class_data["mask"] = masks
    
      print("len of class specific data: ", len(class_data))
        
    # train
    cur_train_loader = Data_loader(X_train_pos = train_pos_set[cur_name], 
                                   X_train_neg = train_neg_set[cur_name], 
                                   X_val_pos = val_pos_set[cur_name], 
                                   X_val_neg = val_neg_set[cur_name],
                                   data = class_data, 
                                   batch_size = args.batch_size, 
                                   k_shot = args.k_shot, 
                                   train_mode= True)
    
    cur_training_generator = cur_train_loader.next_batch_gen()

    # valid
    cur_eval_loader = Data_loader(X_train_pos = train_pos_set[cur_name], 
                                  X_train_neg = train_neg_set[cur_name], 
                                  X_val_pos = val_pos_set[cur_name], 
                                  X_val_neg = val_neg_set[cur_name],
                                  data = class_data, batch_size = args.batch_size, 
                                  k_shot = args.k_shot, train_mode = False)
    
    cur_validation_generator = cur_eval_loader.next_eval_batch_gen()

    # append result
    train_loaders[cur_name] = cur_training_generator
    valid_loaders[cur_name] = cur_validation_generator

  print("\n======== start training ===========\n")

  result_history = train_all_classes(args,
                                     train_loaders=train_loaders,
                                     valid_loaders=valid_loaders,
                                     the_device=device,
                                     model_path=model_path,
                                     ablation = ablation)
  
  print("\n========training result ===========\n")
  result = []
  for name in result_history:
    d = [name] + [item[1] for item in result_history[name]['best_prf']] + [result_history[name]['best_loss'], result_history[name]['best_acc']]
    if args.tagging:
      d = d + [result_history[name]['best_tag_prf'][key][-1] for key in result_history[name]['best_tag_prf']]+ [result_history[name]['best_tag_loss'], result_history[name]['best_tag_acc']]
    result.append(d)

  if args.tagging:
    result = pd.DataFrame(result, columns =["name","pre","rec","f1","loss","acc", "tag_pre","tag_rec","tag_f1","tag_loss","tag_acc"])
  else:
    result = pd.DataFrame(result, columns =["name","pre","rec","f1","loss","acc"])
  print(result.iloc[:,1:].mean(axis = 0))
  #print(result['f1'].mean())
  #print(result['loss'].mean())

  result.to_csv(os.path.join(model_path, "result.csv"))
  pickle.dump(result_history, open(os.path.join(model_path, "train_hist.pkl"),'wb'))
  
# Test sentences saved in a file; for EBM dataset
def test_sentences(model_path: str,             # path for trained model
                  result_path: str,             # path for saving results
                  device = torch.device("cpu"),   
                  batch: int = 10,                    # batch size
                  config = None,                      # model configuration object
                  text_file: str = '../data/test/test_sentences_expert.csv',     # test sentences
                  test_data_path: str ='../data/test',                           # test embedding files
                  train_data_path: str ='../data/train' ,                       # train embedding files
                  ablation: bool = False
                  ):

    args = ModelConfig()
    if config is not None:
      for key in config:
        args.set_option(key, config[key])
    
    use_context = args.use_context
    use_fragment = args.use_fragment

    feature_path = train_data_path
    model_path = model_path

    print(f"model path: {model_path}, result path: {result_path}, feature path: {feature_path}")
    
    # only indexes of the sentences are kept in the dictionary
    train_pos_set = pickle.load(open(os.path.join(feature_path, "train_pos_dict.pkl"),"rb"))
    train_neg_set = pickle.load(open(os.path.join(feature_path, "train_neg_dict.pkl"),"rb"))
    val_pos_set = pickle.load(open(os.path.join(feature_path, "val_pos_dict.pkl"),"rb"))
    val_neg_set = pickle.load(open(os.path.join(feature_path, "val_neg_dict.pkl"),"rb"))

    data = {}
    wordvectors = np.load(os.path.join(feature_path, "wordvectors.npy"))
    print(f"word vector size: {wordvectors.shape}")
    
    if args.sentence_mask:
        masks = np.load(os.path.join(feature_path, "sentence_masks.npy"))
        wordvectors = wordvectors * masks[:,:, None]
    else:
        masks = np.all(wordvectors ==0, axis = -1).astype(int)

    data["wordvector"] = wordvectors

    emb_dim = wordvectors.shape[-1]
    seq_len = wordvectors.shape[-2]
    args.set_option("emb_dim",  emb_dim)
    args.set_option("seq_len", seq_len)


    if use_context:
        section_prob = np.load(os.path.join(feature_path, "section_prob.npy"))
        data["context"] = section_prob
        context_dim = section_prob.shape[-1]
        args.set_option("context_dim", context_dim)

    columns = args.labels

    print("\n======== model argument ===========\n")
    args.print_options()

    # create data loader and load models
    data_loaders = {}
    models = {}
    for cur_name in columns:

        class_data = {key: data[key].copy() for key in data}     # make a copy for each model since components(e.g., fragment) varies by model

        #print("len of general data: ", len(class_data))

        if args.use_fragment :
            frag_dict = pickle.load(open(os.path.join(feature_path, "frag_token_ids.pkl"), 'rb'))

              # mask for fragments in support set
            class_data['fragment'] = frag_dict[cur_name] # num of train sample x sent_length

            # masks for query/supports
            class_data['mask'] = masks

        print(f"components class specific data: {list(class_data.keys())}")

        # valid
        cur_eval_loader = Data_loader(X_train_pos = train_pos_set[cur_name], \
                                  X_train_neg = train_neg_set[cur_name], \
                                  X_val_pos = val_pos_set[cur_name], \
                                  X_val_neg = val_neg_set[cur_name],\
                                  data = class_data, \
                                  batch_size = args.batch_size, \
                                  k_shot = args.k_shot, \
                                  train_mode = False)

        data_loaders[cur_name] = cur_eval_loader

        # load models
        if ablation:
          if args.use_fragment and args.enable_frag_att:
            frag_encoder = Attention(emb_dim = args.emb_dim, 
                               seq_len = args.seq_len, 
                               att_projection_layer=args.att_projection_layer,
                               att_hidden_dim=args.att_hidden_dim,
                               value_dim = args.att_value_dim,
                               dropout_rate=args.att_dropout_rate)
          else:
            frag_encoder = None
        else:
          if args.use_fragment:
            frag_encoder = Attention(emb_dim = args.emb_dim, 
                               seq_len = args.seq_len, 
                               att_projection_layer=args.att_projection_layer,
                               att_hidden_dim=args.att_hidden_dim,
                               value_dim = args.att_value_dim,
                               dropout_rate=args.att_dropout_rate)
          else:
            frag_encoder = None

        if args.use_context:
            context_encoder = Context_Attention(emb_dim = args.context_dim, \
                             context_latent_dim = args.context_latent_dim)
        else:
            context_encoder = None

        encoder = Text_Encoder(emb_dim=args.emb_dim, 
                               seq_len=args.seq_len, 
                               num_filters=args.num_filters, 
                               kernel_sizes=args.kernel_sizes, 
                               text_projection_layer=args.text_projection_layer,
                               text_hidden_dim=args.text_hidden_dim)
        if ablation:
          cur_model = FastSR_Ablation(args = args, 
                       encoder = encoder, 
                       frag_encoder = frag_encoder, 
                       context_encoder = context_encoder)
        else:
          cur_model = FastSR(args = args, encoder = encoder, \
                           frag_encoder = frag_encoder, \
                           context_encoder = context_encoder
                          )

        cur_model.load_state_dict(torch.load(os.path.join(model_path, cur_name + '.pth')))
        cur_model.eval()
        cur_model.to(device)

        models[cur_name] = cur_model

        # print model
        if args.use_context:
            print(cur_model.context_encoder)

        if args.use_fragment:
            print(cur_model.frag_encoder)
            
        print(cur_model)  

    # load test files
    test_df = pd.read_csv(text_file)

    vectors = np.load(os.path.join(test_data_path, "wordvectors.npy"))

    if args.sentence_mask:
        masks = np.load(os.path.join(test_data_path, "sentence_masks.npy"))
        vectors = vectors * masks[:,:, None]
    else:
        masks = np.all(wordvectors == 0, axis = -1).astype(int)
    
    if args.use_context:
            section_prob = np.load(os.path.join(test_data_path, "section_prob.npy"))
            
    if args.use_fragment:    
            frag_dict = pickle.load(open(os.path.join(test_data_path, "frag_token_ids.pkl"), 'rb'))
        
    if not os.path.exists(result_path):
        os.makedirs(result_path)
 
    start = time.time()

    atts = {}
    tags = {}
      
    for cur_label in columns:
        
        print(cur_label)
        
        pred_data_set = {}
        
        pred_data_set['wordvector'] = vectors
    
        if args.use_context:
            pred_data_set['context'] = section_prob
        
        # for query, fragment/mask is all the words
        if args.use_fragment:    
            
            # mask for fragments in query set
            pred_data_set['fragment'] = frag_dict[cur_label] # num of train sample x sent_length
            #print(f"fragment mask shape: {frag_dict[cur_label].shape}")

            # token attention mask
            pred_data_set['mask'] = masks  
            #print(f"sentence mask shape: {masks.shape}")

        # fetch the model
        the_model = models[cur_label]
        the_model.eval()
        
        # featch the data loader
        the_dataloader = data_loaders[cur_label]
        # result list
        cur_result = []

        if args.use_fragment:
            cur_atts = []
            sent_tags = []
            

        test_data_gen = generate_test_batch(pred_data_set, the_dataloader, device, batch = batch)
        
        for support_batch, query_batch, cur_y_query in test_data_gen:
                        
            # forward
            with torch.no_grad():
              
                if args.use_fragment:
                    model_output = the_model(support_batch, query_batch, cur_y_query, 
                                             return_att = True, \
                                             return_loss = False,
                                             return_tag = args.tagging)
                    # get attention
                    if args.enable_frag_att:
                      query_att = model_output["query_att"]

                      query_att = query_att.reshape(-1, args.batch_size, *query_att.shape[1:])
                      query_att = query_att.mean(axis = 1)
                      cur_atts.append(query_att)
                      frag_proto = model_output["frag_proto"]  # - 1 x 2 x att_dim 

                    # get tag output, for each query, a batch tasks issued. Take the average
                    # for debugging, get frag_proto, query, query_mask
                    # all varables are tensors
             
                    query = model_output["query"] # - 1 x seq_len x att_dim   
                    #print("query emb shape:", query.shape)
                    query_mask = model_output["query_mask"] # - 1 x seq_len  
                    #print(frag_proto.size(), query.size(),query_mask.size())

                    tag = model_output["tag"].cpu().numpy()
                    tag = tag.reshape(-1, args.batch_size, *tag.shape[1:])
                    tag = tag.mean(axis = 1)
                    sent_tags.append(tag)

                else:
                    model_output = the_model(support_batch, query_batch, cur_y_query, 
                                         return_att = False, \
                                         return_loss = False,
                                         return_tag = False)
               
                
                cur_pred_prob = model_output["y_hat"] 
                # append result
                cur_pred_prob = cur_pred_prob.cpu().numpy()
                cur_pred_prob = cur_pred_prob.reshape(-1, args.batch_size, 2)
                cur_result.append(cur_pred_prob[:,:,1].mean(axis =-1))

        cur_result = np.concatenate(cur_result, axis = 0)
        test_df[cur_label + "_pred"] = cur_result
        
        if args.use_fragment:
          if args.enable_frag_att:
            cur_atts = np.concatenate(cur_atts, axis = 0)
            #print(cur_atts.shape)
            atts[cur_label] = cur_atts
        
            #frag_protos = np.concatenate(frag_protos, axis = 0)
            #querys = np.concatenate(querys, axis = 0)
          sent_tags = np.concatenate(sent_tags, axis = 0)
          tags[cur_label] = sent_tags
    
        # save result
        test_df.to_csv(os.path.join(result_path, 'sentence_pred.csv'), index=False)    
        pickle.dump(atts, open(os.path.join(result_path, 'tag_att.pkl'), 'wb'))
        pickle.dump(tags, open(os.path.join(result_path, 'tag_pred.pkl'), 'wb'))
        
    print("complete!")   

def generate_test_batch(pred_data_set,        # Prediction sentence dataset
                        dataloader,           # data loader
                        device = torch.device("cpu"), 
                        batch: int = 10):
    
    """ Generate a batch of support dataset for testing. 
        Support/Query contains a list of components depending on whether frag/context used
    """
    # initialize batch container
    support_batch = {key: [] for key in dataloader.data}
    query_batch = {key: [] for key in pred_data_set} 

    start = time.time()
    
    # loop through each sentence
    for i in range(pred_data_set['wordvector'].shape[0]): 
        
        # Get one test item
        v = {key: pred_data_set[key][i] for key in pred_data_set}
        
        # get support batch for each query
        x_set, _, x_hat = dataloader.get_pred_set(v)
        
        # add support/query to container
        for key in dataloader.data:
            support_batch[key].append(x_set[key])
            if key in x_hat:  # some components are only in support
              query_batch[key].append(x_hat[key])
        
        # Container is full or the end of the test set has been reached
        if ((i+1)%batch == 0) or (i == len(pred_data_set["wordvector"])-1):
            
            for key in dataloader.data:
                support_batch[key] = np.concatenate(support_batch[key], axis = 0)
                support_batch[key] = torch.Tensor(support_batch[key]).to(device)

                if key in query_batch:
                  query_batch[key] = np.concatenate(query_batch[key], axis = 0)
                  #print("batch size: ", support_batch[j].shape, query_batch[j].shape)
                  query_batch[key] = torch.Tensor(query_batch[key]).to(device)
   
            cur_y_query = torch.Tensor(np.zeros(query_batch["wordvector"].size(0)))  # faked target
            cur_y_query = cur_y_query.to(device)
        
            yield (support_batch, query_batch, cur_y_query)
            
            # reset the batch container
            support_batch = {key: [] for key in dataloader.data}
            query_batch = {key: [] for key in pred_data_set}
        
# Test all csv file under test_data_path; used in WD case
def test_multi_files(model_path, result_path, device,
                  #use_context = False,
                  #use_fragment = False,
                  batch = 10,
                  config = {},
                  #text_file = '../data/test/test_sentences_expert.csv',
                  test_csv_path ='../data/test/csv',
                  test_pkl_path = '../data/test/pkl',
                  topk_file_path = None,            # only pred topk records along with true sentences
                  #test_emb = 'test_biobert_vectors',
                  train_data_path ='../data/train',
                  ablation = False,
                  ):

    args = ModelConfig()
    if config is not None:
      for key in config:
        args.set_option(key, config[key])
    
    use_context = args.use_context
    use_fragment = args.use_fragment

    feature_path = train_data_path
    model_path = model_path

    print(f"model path: {model_path}, result path: {result_path}, feature path: {feature_path}")
    
    # only indexes of the sentences are kept in the dictionary
    train_pos_set = pickle.load(open(os.path.join(feature_path, "train_pos_dict.pkl"),"rb"))
    train_neg_set = pickle.load(open(os.path.join(feature_path, "train_neg_dict.pkl"),"rb"))
    val_pos_set = pickle.load(open(os.path.join(feature_path, "val_pos_dict.pkl"),"rb"))
    val_neg_set = pickle.load(open(os.path.join(feature_path, "val_neg_dict.pkl"),"rb"))

    data = {}
    wordvectors = np.load(os.path.join(feature_path, "wordvectors.npy"))
    print(f"word vector size: {wordvectors.shape}")
    
    if args.sentence_mask:
        masks = np.load(os.path.join(feature_path, "sentence_masks.npy"))
        wordvectors = wordvectors * masks[:,:, None]
    else:
        masks = np.all(wordvectors ==0, axis = -1).astype(int)

    data["wordvector"] = wordvectors

    emb_dim = wordvectors.shape[-1]
    seq_len = wordvectors.shape[-2]
    args.set_option("emb_dim",  emb_dim)
    args.set_option("seq_len", seq_len)


    if use_context:
        section_prob = np.load(os.path.join(feature_path, "section_prob.npy"))
        data["context"] = section_prob
        context_dim = section_prob.shape[-1]
        args.set_option("context_dim", context_dim)

    columns = args.labels

    print("\n======== model argument ===========\n")
    args.print_options()

    # create data loader and load models
    data_loaders = {}
    models = {}
    for cur_name in columns:

        class_data = {key: data[key].copy() for key in data}     # make a copy for each model since components(e.g., fragment) varies by model

        print("len of general data: ", len(class_data))

        if use_fragment:
            frag_dict = pickle.load(open(os.path.join(feature_path, "frag_token_ids.pkl"), 'rb'))

              # mask for fragments in support set
            class_data['fragment'] = frag_dict[cur_name] # num of train sample x sent_length

            # masks for query/supports
            class_data['mask'] = masks

        print(f"components class specific data: {list(class_data.keys())}")

        # valid
        cur_eval_loader = Data_loader(X_train_pos = train_pos_set[cur_name], \
                                  X_train_neg = train_neg_set[cur_name], \
                                  X_val_pos = val_pos_set[cur_name], \
                                  X_val_neg = val_neg_set[cur_name],\
                                  data = class_data, \
                                  batch_size = args.batch_size, \
                                  k_shot = args.k_shot, \
                                  train_mode = False)

        data_loaders[cur_name] = cur_eval_loader

        # load models

        if args.use_fragment:
            frag_encoder = Attention(emb_dim = args.emb_dim, 
                               seq_len = args.seq_len, 
                               att_projection_layer=args.att_projection_layer,
                               att_hidden_dim=args.att_hidden_dim,
                               value_dim = args.att_value_dim,
                               dropout_rate=args.att_dropout_rate)
        else:
            frag_encoder = None

        if args.use_context:
            context_encoder = Context_Attention(emb_dim = args.context_dim, \
                             context_latent_dim = args.context_latent_dim)
        else:
            context_encoder = None

        encoder = Text_Encoder(emb_dim=args.emb_dim, 
                               seq_len=args.seq_len, 
                               num_filters=args.num_filters, 
                               kernel_sizes=args.kernel_sizes, 
                               text_projection_layer=args.text_projection_layer,
                               text_hidden_dim=args.text_hidden_dim)
        if ablation:
          cur_model = FastSR_Ablation(args = args, 
                       encoder = encoder, 
                       frag_encoder = frag_encoder, 
                       context_encoder = context_encoder)
        else:

          cur_model = FastSR(args = args, encoder = encoder, \
                           frag_encoder = frag_encoder, \
                           context_encoder = context_encoder
                          )

        cur_model.load_state_dict(torch.load(os.path.join(model_path, cur_name + '.pth')))
        cur_model.eval()
        cur_model.to(device)

        models[cur_name] = cur_model

        # print model

        if args.use_context:
            print(cur_model.context_encoder)
            #print(summary(cur_model.context_encoder,[(32, args.context_dim),\
            # (32, args.n_way*args.k_shot, args.context_dim)]))


        if args.use_fragment:
            print(cur_model.frag_encoder)
            #print(summary(frag_encoder,[(32, args.seq_len, args.emb_dim), \
            #  (32, 2,5, args.seq_len, args.emb_dim),  (32, args.seq_len),  (32,2,5, args.seq_len)]))

        print(cur_model)  

    if not os.path.exists(result_path):
      os.makedirs(result_path, exist_ok = True)
            
    # load test files
    start_time = time.time()
    
    topk_df = None
    if topk_file_path:
      topk_df = pd.read_csv(topk_file_path)
      topk_df["pmid"] = topk_df["pmid"].astype(int).astype(str)
    
    print(f"\n\n========= Start test @ {start_time :.2f} =======\n\n")
    
    file_cnt = 0
    for text_file in glob.glob(os.path.join(test_pkl_path, "*.pkl")):
      
      file_name = text_file.split("/")[-1]
      file_id = file_name.replace(".pkl",'')
      
      
      # check if the file has been tested
      if not os.path.exists(os.path.join(result_path, file_id +'_sentence_pred.csv')):
        file_cnt += 1
        print(f"{file_cnt}: {file_id} @ {time.time() - start_time :.2f}")
        
        if os.path.exists(os.path.join(result_path, file_id +'.csv')):
          test_df = pd.read_csv(os.path.join(result_path, file_id +'.csv'))
        else:
          test_df = pd.read_csv(os.path.join(test_csv_path, file_id + ".csv"))

        test_pack = pickle.load(open(text_file, "rb"))
        
        #vectors = np.load(os.path.join(test_data_path, "wordvectors.npy"))
        vectors = test_pack["wordvector"]

        if args.sentence_mask:
            #masks = np.load(os.path.join(test_data_path, "sentence_masks.npy"))
            masks = test_pack["mask"]
            vectors = vectors * masks[:,:, None]
            
        else:
            masks = np.all(wordvectors == 0, axis = -1).astype(int)
        
        #print(f"masks shape: {masks.shape}")
        
        if args.use_context:
            section_prob = test_pack["section_prob"]
            #section_prob = np.load(os.path.join(test_data_path, "section_prob.npy"))
                
        #if args.use_fragment:    
        #        frag_dict = pickle.load(open(os.path.join(test_data_path, "frag_token_ids.pkl"), 'rb'))

        if topk_df is not None:
          topk_sid = topk_df[topk_df.pmid == file_id]["sid"].values
          if len(topk_sid) > 0:
            vectors = vectors[topk_sid]
            masks = masks[topk_sid]
            section_prob = section_prob[topk_sid]
            test_df = test_df.loc[topk_sid]
            
          print(f"file: {file_id}, top sent: {len(topk_sid)}")
          
        start = time.time()

        # test if prediction has been done for some class
        if os.path.exists(os.path.join(result_path, file_id+'_att.pkl')):
          atts = pickle.load(open(os.path.join(result_path, file_id+'_att.pkl'), 'rb'))
        else:
          atts = {}
          
        if os.path.exists(os.path.join(result_path, file_id+'_tag.pkl')):
          tags = pickle.load( open(os.path.join(result_path, file_id+'_tag.pkl'), 'rb'))
        else:
          tags = {}
        
        #print("number of features: ", len(pred_data_set))
        # zip to have all features for one sample

        for cur_label in columns:
            
            print(cur_label)
            
            pred_data_set = {}
            
            pred_data_set['wordvector'] = vectors
        
            if args.use_context:
                pred_data_set['context'] = section_prob
            
            # for query, fragment/mask is all the words
            if args.use_fragment:    
                
                # mask for fragments in query set
                #pred_data_set['fragment'] = frag_dict[cur_label] # num of train sample x sent_length
                pred_data_set['fragment'] = masks # num of test sample x sent_length
                #print(f"fragment mask shape: {frag_dict[cur_label].shape}")

                # token attention mask
                pred_data_set['mask'] = masks  
                #print(f"sentence mask shape: {masks.shape}")

            # fetch the model
            the_model = models[cur_label]
            the_model.eval()
            
            # featch the data loader
            the_dataloader = data_loaders[cur_label]
            # result list
            cur_result = []

            if args.use_fragment:
                cur_atts = []
                frag_protos = []
                querys = []
                query_masks =[]
                sent_tags = []
                

            test_data_gen = generate_test_batch(pred_data_set, the_dataloader, device, batch = batch)
            
            for support_batch, query_batch, cur_y_query in test_data_gen:
                            
                # forward
                with torch.no_grad():
                  
                    if args.use_fragment:
                        model_output = the_model(support_batch, query_batch, cur_y_query, 
                                                return_att = True, \
                                                return_loss = False,
                                                return_tag = args.tagging)
                        # get attention
                        query_att = model_output["query_att"]

                        query_att = query_att.reshape(-1, args.batch_size, *query_att.shape[1:])
                        query_att = query_att.mean(axis = 1)
                        cur_atts.append(query_att)

                        tag = model_output["tag"].cpu().numpy()
                        tag = tag.reshape(-1, args.batch_size, *tag.shape[1:])
                        tag = tag.mean(axis = 1)
                        sent_tags.append(tag)

                    else:
                        model_output = the_model(support_batch, query_batch, cur_y_query, 
                                            return_att = False, \
                                            return_loss = False,
                                            return_tag = False)
                  
                    
                    cur_pred_prob = model_output["y_hat"] 
                    # append result
                    cur_pred_prob = cur_pred_prob.cpu().numpy()
                    cur_pred_prob = cur_pred_prob.reshape(-1, args.batch_size, 2)
                    cur_result.append(cur_pred_prob[:,:,1].mean(axis =-1))

            cur_result = np.concatenate(cur_result, axis = 0)
            test_df[cur_label] = cur_result
            
            if args.use_fragment:
                cur_atts = np.concatenate(cur_atts, axis = 0)
                #print(cur_atts.shape)
                atts[cur_label] = cur_atts
            
                #frag_protos = np.concatenate(frag_protos, axis = 0)
                #querys = np.concatenate(querys, axis = 0)
                sent_tags = np.concatenate(sent_tags, axis = 0)
              
                tags[cur_label] = sent_tags
        
            # save result
        test_df.to_csv(os.path.join(result_path, file_id +'.csv'), index=False)   
        if len(atts) > 0: 
          pickle.dump(atts, open(os.path.join(result_path, file_id+'_att.pkl'), 'wb'))
        if len(tags) > 0:
          pickle.dump(tags, open(os.path.join(result_path, file_id+'_tag.pkl'), 'wb'))
          
    print(f"\n\n======== complete @ {time.time()-start_time :.2f} ========\n\n") 

    