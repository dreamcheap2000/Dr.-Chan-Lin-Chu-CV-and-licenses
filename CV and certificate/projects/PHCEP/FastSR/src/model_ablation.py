import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from model import Emb_Projection

torch.set_printoptions(precision=2)


class FastSR_Ablation(nn.Module):
  def __init__(self, args, encoder,  frag_encoder = None, 
               context_encoder = None):

    super().__init__()
    self.encoder = encoder
    
    self.components = ["semantics"]  # weights for sementics
    
    self.dist_metric = args.dist_metric

    self.use_fragment = args.use_fragment
    self.frag_encoder = frag_encoder

    self.use_context = args.use_context
    self.context_encoder = context_encoder

    self.tagging = args.tagging      # whether to do sequence tagging
    self.syn_cost = args.syn_cost
    self.tagging_method = args.tagging_method
    self.initial_weights = args.initial_weights
    self.tag_cost_weight = args.tag_cost_weight
    
    # ablation study
    self.enable_joint_learning = args.enable_joint_learning
    self.enable_frag_att = args.enable_frag_att
    
    if not self.enable_frag_att:
      self.projection = Emb_Projection(args.att_projection_layer, 
                                        emb_dim= args.emb_dim, 
                                        hidden_dim = args.att_hidden_dim)
    
    # if joint learning is False, disable joint learning by not setting the fragment weight
    if self.use_fragment and self.enable_joint_learning:    
        self.components.append("fragment")      
        
    if self.use_context:
        self.components.append("context")
        
    self.component_weights = nn.Parameter(torch.Tensor(self.initial_weights[0:len(self.components)]))
          
    print(f"Distance metric: {self.dist_metric}, cost syn: {self.syn_cost}")
  
  @staticmethod
  def similarity(x, y, metric='cosine'):
    n = x.size(0)        # x shape is (batch_size,  z_dim)
    m = y.size(0)        # y shape is (batch_size, n_way*k_shot, z_dim)
    d = x.size(1)
    assert d == y.size(-1)

    x = x.unsqueeze(1)
    
    if metric == 'l2':
      sim = - torch.pow(x - y, 2).sum(-1)/math.sqrt(d)  # divided by sqrt(z_dim) as a temperature
      
    elif metric=='cosine':     #metric =='cosine'
      x = F.normalize(x,dim=-1,p=2)
      y = F.normalize(y,dim=-1,p=2)
      sim = torch.sum(x*y, dim = -1)
    else:
      x = F.normalize(x,dim=-1,p=2)
      y = F.normalize(y,dim=-1,p=2)
      sim = torch.sum(x*y, dim = -1)
      sim_mean = sim.mean(axis = -1, keepdims=True)
      sim = (sim - sim_mean)/(sim_mean + 1e-7)

    return sim            # batch_size x (n_class x support)

  #frag_code: batch x 2 x 5 x frag_latent_dim
  #query: batch x seq_len x frag_latent_dim  
  def seq_tagging_l2(self, frag_code, query, query_mask): 
        
        """Tagging based on L2 distance between prototypes and word embeddings"""

        frag_proto = frag_code.mean(dim = -2)   #  batch x 2  x frag_latent_dim
       
        query = query * query_mask.unsqueeze(-1)
        
        distance = torch.pow(frag_proto.unsqueeze(1) - query.unsqueeze(2), 2).sum(-1)
        
        tags = torch.softmax( -distance, dim = -1)  # shape -1  x  seq_len x 2
        tags = tags * query_mask.unsqueeze(-1)
        
        return tags
   
   
   # Tagging by cosine similarity   
  def seq_tagging(self, frag_code, query): 
        
        frag_code = frag_code.mean(dim = -2)   #  batch x 2  x att_dim
        
        # normalize
        frag_code = F.normalize(frag_code, dim = -1)
        query = F.normalize(query, dim = -1)

        # move att_dim to the middle
        x = torch.swapaxes(frag_code, -2, -1) #  batch   x att_dim x 2
        
        sim = query.bmm(x)
        
        tags = torch.softmax(sim, dim = -1)  # shape -1  x  seq_len
        
        return tags
    
  
  def forward(self, x_support_set, x_query_set=None, y_query=None, \
              return_loss = True, return_att = False, return_tag = False):
    """
    Forward for prototypical network

    Args:
      x_support(torch.Tensor): the support set, assume the shape (batch_size, n_way, k_shot, *data dimension)
      x_query(torch.Tensor): the query set, assume the shape (batch_size, *data dimension)
      y_query(torch.longTensor): the label for query set (batch_size,)

    returns:
      loss(torch.Tensor): negative log likelihood to be minimized, will be used to update the parameters via backprobagation
      acc(float): accuracy
    """

    # semantics
    x_support = x_support_set["wordvector"]
    x_query = x_query_set["wordvector"]
    
     # find number of class, number of query, number of support
    batch_size = x_support.size(0)
    n_way = x_support.size(1)
    k_shot = x_support.size(2)

    # concatenate support/query
    x = torch.cat([x_support.view(batch_size * n_way * k_shot, *x_support.size()[3:]), # shape (n_class * n_support, *data dimension)
                  x_query],  # shape: (n_class * n_support, *data dimension)
                  dim=0)
  
   # context
    if self.use_context:
      x_support_con = x_support_set["context"]
      x_query_con = x_query_set["context"]

      x_con = torch.cat([x_support_con.view(batch_size * n_way * k_shot, *x_support_con.size()[3:]), # shape (n_class * n_support, *data dimension)
                  x_query_con],  # shape: (n_class * n_support, *data dimension)
                  dim=0)             
    else:
      x_con = None

    # fragment
    if self.use_fragment:  
      # masks for fragments in support sets 
      fragment_mask =  x_support_set["fragment"]
      fragment = fragment_mask.unsqueeze(-1) * x_support
    
      # mask for fragment in query, i.e., tagging target. If sentence label = 0, y_tag = 1 for all tokens
      y_tag = x_query_set["fragment"]
        
      # reset the tag to 0 if sentence label = 0
      if y_query is not None:
          y_tag = y_tag * y_query.unsqueeze(-1)

      # masks for support/query; need for attention
      query_mask = x_query_set["mask"]
      #support_mask = x_support_set[i]   
    else:
      fragment = None

    # 
    z = self.encoder(x)  # pass CNN encoder
    
    z_dim = z.size(-1)  # dimension of latent vector

    # estimate the prototypes
    supports = z[:batch_size * n_way * k_shot].view(batch_size, n_way, k_shot, z_dim)  

    # extract the latent query vector
    querys = z[(batch_size * n_way * k_shot):]

    prototypes = supports.mean(dim = 2)

    # extract the latent query vector
    querys = z[(batch_size * n_way * k_shot):]

    # calculate the distance
 
    sim = self.similarity(querys, prototypes, metric=self.dist_metric)   # batch_size x n_way  
    
    component_weight_norm = torch.softmax(self.component_weights, dim = -1).view(-1)
    component_weight_norm = {item: component_weight_norm[i] for i, item in enumerate(self.components)}
    
    sim = component_weight_norm["semantics"] * sim
    
    if self.use_fragment:
      
        if self.enable_frag_att:
          frag_code, query_code, frag_att, query_att, query = self.frag_encoder(x_query, fragment, query_mask, fragment_mask)
           
          # reshape query_att (attention to each word in query) to batch x n_way x k_shot x seq_len
          query_att = query_att.view(batch_size, n_way, k_shot, -1)

          # take average of k-shot
          query_att = torch.swapaxes(query_att.mean(2), 1,2)     # batch x seq_len x n_way  
          
          # Ablation for joint learning
          if self.enable_joint_learning:
              frag_code1 = frag_code.mean(dim=2)  # batch x 2  x frag_latent_dim
              query_code1 = query_code.mean(dim = 2)     # batch  x 2 x frag_latent_dim
              z_dim = frag_code.size(-1)
              frag_sim = - torch.pow(frag_code1 - query_code1, 2).sum(-1)/math.sqrt(z_dim)

              sim += component_weight_norm["fragment"]*frag_sim
            
          
        else:   # ablation for attention: take average of each word in fragment
          
          # just projection, size batch x n_way x k-shot x seq_len x emb_dim
          fragment = self.projection(fragment)
          query = self.projection(x_query)
          frag_code = fragment.sum(dim = -2)/(fragment_mask.sum(dim = -1).unsqueeze(-1) + 1e-7)  #batch x 2 x 5 x emb_dim
                
          # take the mean to generate code for joint_learning
          if self.enable_joint_learning:
            frag_code1 = fragment.sum(dim = -2)/(fragment_mask.sum(dim = -1).unsqueeze(-1) + 1e-7)  #batch x 2 x 5 x emb_dim
            frag_code1 = frag_code1.mean(dim = -2)     #batch x 2 x emb_dim
            query_code1 = query.sum(dim = -2, keepdims = True)/(query_mask.sum(dim = -1, keepdims = True).unsqueeze(-1) + 1e-7)   #batch  x 1 x emb_dim         
            z_dim = frag_code.size(-1)
            frag_sim = - torch.pow(frag_code1 - query_code1, 2).sum(-1)/math.sqrt(z_dim)
            sim += component_weight_norm["fragment"]*frag_sim
           
        # multitask learning, get tagging cost
        if self.tagging:        
          
          if self.tagging_method == 'fastsr':
            tag = self.seq_tagging_l2(frag_code, query, query_mask)  # use L2 distance, batch x seq_len x n_way
            
            # tag probility x query attention  only if joint learning is enabled
            if self.enable_joint_learning and self.enable_frag_att:
              tag = tag * query_att
              
            tag = tag[:,:, -1]
          
          # ProtoNER  
          elif self.tagging_method == 'ProtoNER':
                # get masked mean
                frag_code = fragment.sum(dim = -2)/(fragment_mask.sum(dim = -1).unsqueeze(-1) + 1e-7)  #batch x 2 x 5 x emb_dim
                if self.dist_metric == 'l2':
                    tag =self.seq_tagging_l2(frag_code, query, query_mask)  # prob. of  being emitted
                else:
                    tag =self.seq_tagging(frag_code, query)  # prob. of  being emitted
                tag = tag[:,:, -1]
                
          elif self.tagging_method == 'NearestNeighbor':
                
                seq_len = query.size(-2)
                hidden_dim = query.size(-1)
        
                # normalize
                frag_code = F.normalize(fragment, dim = -1)
                frag_code = frag_code * fragment_mask.unsqueeze(-1)
                
                query_code = F.normalize(query, dim = -1)
                query_code = query_code * query_mask.unsqueeze(-1)

                # reshape and move att_dim to the middle
                frag_code = torch.reshape(frag_code, (batch_size, -1, hidden_dim))
                frag_code = torch.swapaxes(frag_code, -2, -1) #  batch   x hidden_dim x (seq_len*2*5)
        
                # calculate similarity as dot product, shape: -1  x  seq_len x 2 x 5 x 100
                tag_sim = query_code.bmm(frag_code).view(batch_size, seq_len, n_way, k_shot, -1)
                #print("sim size ", tag_sim.size())
                #print("sim: ", sim[0,0:5])  # test
                
                tag_sim = tag_sim.sum(-1)/(fragment_mask.sum(-1).unsqueeze(1) + 1e-7)    # average similarity per word
                
                tag_sim = tag_sim.sum(-1)   #shape: -1  x  seq_len x 2    
                
                #print("sim size ", tag_sim.size())
                #print("sim: ", tag_sim[0,5:15])  # test
                tag = torch.softmax(tag_sim, axis = -1)[:,:,1]     # shape -1  x  seq_len
                tag = tag * query_mask

    if self.use_context:
      context_dim = x_support_con.size(-1)
      x_support_con = x_support_con.view(batch_size, -1, context_dim)
      context_att_score = self.context_encoder(x_query_con, x_support_con)

      # point attention
      context_att_score = context_att_score.view(batch_size, n_way, k_shot)
      context_sim, _ = torch.max(context_att_score, dim = -1)
    
      sim += component_weight_norm["context"]*context_sim
      
    sim = torch.clamp(sim, -10, 10)
    p_y = F.softmax(sim, dim = -1)    
    
    returned_items = {}
    returned_items["y_hat"] = p_y
    
    # loss
    if return_loss:
        #criteria = nn.BCELoss(reduction = 'sum')
        criteria = nn.BCELoss(reduction = 'none')
        #weight = 1 + y_query             # double weight for class 1
        loss = criteria(p_y[:, 1], y_query)  # positive
        loss =  loss.mean()
        #loss = (weight * loss).sum()

        returned_items["query_loss"] = loss
    
        if self.tagging:

            if self.syn_cost:                           # MTL regularization cost
              max_tag_prob, _ = tag.max(dim = -1)
              reg_loss = criteria(p_y[:, 1], max_tag_prob)  
              
              tag_loss = criteria(tag * p_y[:, 1].unsqueeze(-1), y_tag)
              tag_loss = (tag_loss.sum(-1)/(query_mask.sum(-1) + 1e-7))
              
              tag_loss = reg_loss + tag_loss
              
            else:     # none: no synchronization
              tag_loss = criteria(tag, y_tag)
              tag_loss = (tag_loss.sum(-1)/(query_mask.sum(-1) + 1e-7))
            
            tag_loss = tag_loss.mean()

            returned_items["query_loss"] = loss
            
            loss = (1-self.tag_cost_weight) * loss + self.tag_cost_weight * tag_loss
            returned_items["tag_loss"] = tag_loss
            
        returned_items["loss"] = loss

    if return_att and self.enable_frag_att:
        
        returned_items["frag_att"] = frag_att.detach().cpu().numpy() 
        returned_items["query_att"] = query_att.detach().cpu().numpy()
   
    if return_tag:
        returned_items["tag_label"] = y_tag
        returned_items["tag"] = tag
        returned_items["query"] = query
        returned_items["query_mask"] = query_mask
        
        if self.enable_frag_att:
          returned_items["frag_proto"] = frag_code

    return returned_items

