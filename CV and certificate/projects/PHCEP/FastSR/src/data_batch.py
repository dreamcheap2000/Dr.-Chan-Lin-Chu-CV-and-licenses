from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


import torch
import numpy as np
from typing import Union, List, Any, Dict

            
class Data_loader():
    
    """
        Random sampling to generate batches for few short training and testing
    """

    def __init__(self, 
                 X_train_pos: Any,  # numpy array of postive sentence ids for training
                 X_train_neg: Any,  # numpy array of negative sentence ids for training
                 X_val_pos: Any,      # numpy array of postive sentence ids for validation
                 X_val_neg: Any,      # numpy array of postive sentence ids for validation
                 data: Dict,               # data dictionary for sentence, fragment, and context
                 batch_size: int = 36,
                 k_shot: int = 1, 
                 num_classes: int = 2,
                 train_mode: bool = True):  
        
        self.data = data
        
        self.batch_size = batch_size
        self.k_shot = k_shot # 1 or 5, how many times the model sees the example
        self.num_classes = num_classes
        
        self.train_pos = X_train_pos
        self.train_neg = X_train_neg

        # position of last batch
        self.train_pos_index = 0
        self.train_neg_index = 0
            
        if not train_mode:
            
            self.val_pos = X_val_pos
            self.val_neg = X_val_neg
               
            self.val_pos_index = 0
            self.val_neg_index = 0
                  
            # merge train & val for prediction use
            self.all_pos = np.concatenate([self.train_pos, self.val_pos])
            self.all_neg = np.concatenate([self.train_neg, self.val_neg])

            self.pos_index = 0
            self.neg_index = 0
            
        
        self.iters = 100

    # Get next batch for training
    def next_batch(self):
        x_set_batch = []
        y_set_batch = []
        x_hat_batch = []
        y_hat_batch = []
        
        
        x_set = []
        y_set = []
        
        for _ in range(self.batch_size):
            
            x_set = []
            y_set = []
        
            target_class = np.random.randint(self.num_classes)
            #print(target_class)                
                    
            # negative class
            for i in range(self.k_shot+1):
                
               # shuffle pos or neg if a sequence has been full used
                if self.train_neg_index == len(self.train_neg):
                    
                    self.train_neg = np.random.permutation(self.train_neg)
                    self.train_neg_index = 0
                    #print("neg seq", self.train_neg_seq)
                    
                if i==self.k_shot:  # the last one is test sample
                    
                    if target_class == 0: # positive class
                        x_hat_batch.append(self.train_neg[self.train_neg_index])
                        
                        y_hat_batch.append(0)
                        self.train_neg_index += 1                    
                else:
                    
                    x_set.append(self.train_neg[self.train_neg_index])
                    
                    y_set.append(0)
                    self.train_neg_index += 1
                                       
             # positive class
            for i in range(self.k_shot+1):
                
               # shuffle pos or neg if a sequence has been full used
                if self.train_pos_index == len(self.train_pos):
                    
                    self.train_pos = np.random.permutation(self.train_pos)
                    self.train_pos_index = 0
                    #print("pos seq", self.train_pos_seq)
                    
                if i==self.k_shot:  # the last one is test sample
                    
                    if target_class == 1: # positive class
                        x_hat_batch.append(self.train_pos[self.train_pos_index])
                        
                        y_hat_batch.append(1)
                        self.train_pos_index += 1
                
                        
                else:
                    x_set.append(self.train_pos[self.train_pos_index])
                    
                    y_set.append(1)
                    self.train_pos_index += 1

            x_set_batch.append(x_set)
            y_set_batch.append(y_set)       
        
        # get feature arrays for the batch
        
        #print(x_set_batch)
        #print(x_hat_batch)
        
        feature_set_batch = {}
        feature_hat_batch = {}
        
        for key in self.data:
            feature = self.data[key]
            f_set = np.array([np.array(feature[b]) for b in x_set_batch])
            f_hat = np.array(feature[x_hat_batch])

            # reshape support to (batch, n_way, k_shot, *feature size)
            f_set = f_set.reshape((self.batch_size, 2, self.k_shot, *(feature.shape[1:])))
            #print(f_set.shape)
            #print(f_hat.shape)
            
            feature_set_batch[key] = f_set
            feature_hat_batch[key] = f_hat
            
        return feature_set_batch, np.asarray(y_set_batch).astype(np.int32), \
               feature_hat_batch, np.asarray(y_hat_batch).astype(np.int32)
               #np.zeros(self.batch_size)   # all 0s for aux output

    # Get next batch for evaluation
    def next_eval_batch(self):
        x_set_batch = []
        y_set_batch = []
        x_hat_batch = []
        y_hat_batch = []
        
        for _ in range(self.batch_size):
            
            x_set = []
            y_set = []
            
            target_class = np.random.randint(self.num_classes)
            #print(target_class)
            
            if self.val_pos_index == len(self.val_pos):
                self.val_pos = np.random.permutation(self.val_pos)
                self.val_pos_index = 0
                #print("pos val seq", self.val_pos_seq)

            if self.val_neg_index == len(self.val_neg):
                self.val_neg = np.random.permutation(self.val_neg)
                self.val_neg_index = 0
                #print("net val seq", self.val_neg_seq)
                           
            # negative class
            for i in range(self.k_shot+1):
                
               # shuffle pos or neg if a sequence has been full used
                if self.train_neg_index == len(self.train_neg):
                    self.train_neg = np.random.permutation(self.train_neg)
                    self.train_neg_index = 0
                    #print("neg seq", self.train_neg_seq)
                    
                if i==self.k_shot:  # the last one is test sample
                    
                    if target_class == 0: # negative class
                        x_hat_batch.append(self.val_neg[self.val_neg_index])
                        
                        y_hat_batch.append(0)
                        self.val_neg_index += 1       
                else:
                    
                    x_set.append(self.train_neg[self.train_neg_index])
                    
                    y_set.append(0)
                    self.train_neg_index += 1

            # positive class
            for i in range(self.k_shot+1):
                
               # shuffle pos or neg if a sequence has been full used
                if self.train_pos_index == len(self.train_pos):
                    self.train_pos = np.random.permutation(self.train_pos)
                    self.train_pos_index = 0
                    #print("pos seq", self.train_pos_seq)
                    
                if i==self.k_shot:  # the last one is test sample
                    
                    if target_class == 1: # positive class
                        x_hat_batch.append(self.val_pos[self.val_pos_index])
                        
                        y_hat_batch.append(1)
                        self.val_pos_index += 1               
                        
                else:
                    x_set.append(self.train_pos[self.train_pos_index])
                    
                    y_set.append(1)
                    self.train_pos_index += 1

                      
            x_set_batch.append(x_set)
            y_set_batch.append(y_set)
        
        #print(x_set_batch)
        #print(x_hat_batch)
        
        feature_set_batch = {}
        feature_hat_batch = {}
        
        # loop through all features 
        for key in self.data:
            feature = self.data[key]
            f_set = np.array([np.array(feature[b]) for b in x_set_batch])
            f_hat = np.array(feature[x_hat_batch])
            #print(f_set.shape)
            #print(f_hat.shape)

            f_set = f_set.reshape((self.batch_size, 2, self.k_shot, *(feature.shape[1:])))
            
            feature_set_batch[key] = f_set
            feature_hat_batch[key] = f_hat
        
        # note: pos is 1 and neg is 0     
        return feature_set_batch, np.asarray(y_set_batch).astype(np.int32), \
               feature_hat_batch, np.asarray(y_hat_batch).astype(np.int32)
               #np.zeros(self.batch_size)   # all 0s for aux output
    
    
    # generate support set for each sample in prediction
    # use all samples as support
    def get_pred_set(self, pred):
        x_set_batch = []
        y_set_batch = []
        x_hat_batch = []
        
        for _ in range(self.batch_size):  #batch_size = 32
            
            x_set = []
            y_set = []
            
            target_class = np.random.randint(self.num_classes)   #target_class = 0/1
            #print(target_class)
            
            if self.pos_index == len(self.all_pos):  #initiate the index
                self.all_pos = np.random.permutation(self.all_pos)
                self.pos_index = 0

            if self.neg_index == len(self.all_neg):   #initiate the index
                self.all_neg = np.random.permutation(self.all_neg)
                self.neg_index = 0
                           
            # negative class
            for i in range(self.k_shot):
                
               # shuffle pos or neg if a sequence has been full used
                if self.neg_index == len(self.all_neg):
                    self.all_neg = np.random.permutation(self.all_neg)
                    self.neg_index = 0
                    #print("neg seq", self.train_neg_seq)
                    
                x_set.append(self.all_neg[self.neg_index])
                
                y_set.append(0)
                self.neg_index += 1

            # positive class
            for i in range(self.k_shot):
                
               # shuffle pos or neg if a sequence has been full used
                if self.pos_index == len(self.all_pos):
                    self.all_pos = np.random.permutation(self.all_pos)
                    self.pos_index = 0
                    #print("pos seq", self.train_pos_seq)

                x_set.append(self.all_pos[self.pos_index])
                
                y_set.append(1)
                self.pos_index += 1
                    
            # Prediction sample
            
            x_set_batch.append(x_set)
            y_set_batch.append(y_set) 
        
        x_hat_batch.append(pred)
        #print(x_set_batch)

        
        feature_hat_batch = {}
        feature_set_batch = {}
        
        #print(f"components in support: {list(self.data.keys())}")
        #print(f"components in query: {list(pred.keys())}" )
        # loop through all features 
        for key in self.data:

            # repeat each element in pred for batch_size times
            if key in pred:
                feature_hat_batch[key] = np.repeat(pred[key][None,:], self.batch_size, axis = 0)

            feature = self.data[key]
            f_set = np.array([np.array(feature[b]) for b in x_set_batch])
            #print(f_set.shape)

            f_set = f_set.reshape((self.batch_size, self.num_classes, self.k_shot, *(feature.shape[1:])))
            
            feature_set_batch[key] = f_set
            
           
        return feature_set_batch, np.asarray(y_set_batch).astype(np.int32), feature_hat_batch
    
    #def get_pred_set_gen(self, pred):
    #    while True:
    #        x_set, y_set, x_hat, y_hat = train_loader.next_batch()
    #        yield([x_set, x_hat], 1-y_hat)

    def convert_to_tensor(self, features):
      
      '''features is a dictionary of numpy arrays'''

      tensors = {key:torch.Tensor(features[key]) for key in features}

      return tensors

            
    def next_eval_batch_gen(self):
        while True:
            x_set, _, x_hat, y_hat = self.next_eval_batch()
            
            x_set = self.convert_to_tensor(x_set)
            x_hat = self.convert_to_tensor(x_hat)
            y_hat = torch.Tensor(y_hat)

            yield(x_set, x_hat, y_hat)
            
    def next_batch_gen(self):
        while True:
            
            x_set, _, x_hat, y_hat = self.next_batch()
            
            x_set = self.convert_to_tensor(x_set)
            x_hat = self.convert_to_tensor(x_hat)
            y_hat = torch.Tensor(y_hat)
            
            yield(x_set, x_hat, y_hat)
            
 