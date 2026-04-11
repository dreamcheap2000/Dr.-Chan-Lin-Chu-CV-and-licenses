import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Union, List, Any, Dict

torch.set_printoptions(precision=2)

class Context_Attention(nn.Module):
    
  """ Context attention by pointer network """
    
  def __init__(self, 
               emb_dim: int = 13,
               context_latent_dim: int = 10, 
               n_way:int = 2):
      
        super().__init__()
        self.emb_dim = emb_dim
        self.context_latent_dim = context_latent_dim
        self.n_way = n_way

        self.att_layer = nn.Linear(self.emb_dim, self.context_latent_dim)    

  def forward(self, query_context, support_context):
    
    query_context = self.att_layer(query_context)
    support_context = self.att_layer(support_context)

    att = torch.bmm(support_context, query_context.unsqueeze(-1)).squeeze(-1)
    
    att = torch.softmax(att, dim = -1)
   
    return att


class Attention(nn.Module):

    """ Implementing two attention mechanism: 
    (1) location-based, 
    (2) query to fragment attention 
    """

    def __init__(self, 
                 emb_dim: int = 100, 
                 seq_len:int = 100, 
                 n_way:int = 2, 
                 att_projection_layer: str = 'linear', 
                 att_hidden_dim: int = 100,
                value_dim: int = 50,
                 dropout_rate: float = 0.3):
      
        super().__init__()
        self.emb_dim = emb_dim
        self.seq_len = seq_len
        self.n_way = n_way
        self.att_projection_layer = att_projection_layer
        self.dropout_rate = dropout_rate

        # set projection layer to reduce dimensionality
        if att_projection_layer is not None:
          self.projector = Emb_Projection(layer_name = att_projection_layer, 
                                        emb_dim= emb_dim, 
                                        hidden_dim = att_hidden_dim)
        else:
           self.projector = None
        
        self.emb_dim = self.projector.output_dim

        # attention per prototype
        self.self_att_layer = nn.ModuleList([nn.Linear(self.emb_dim, 1, bias=False) for i in range(self.n_way)])

        # query to fragment attention - transformation parameters
        self.query_att = nn.Linear(self.emb_dim, value_dim, bias = False)
        self.frag_att = nn.Linear(self.emb_dim, value_dim, bias = False)
        self.query_frag_att = nn.Linear(self.emb_dim, value_dim, bias = False)
        
        # query to fragment attention - value parameters
        self.value_gate = nn.Linear(value_dim, 1, bias = False)
        self.value_att = nn.Linear(value_dim, 1, bias = False)

        if dropout_rate > 0:
          self.dropout = nn.Dropout(p = dropout_rate)

    def forward(self, query, fragment, query_mask, fragment_mask):

        if self.att_projection_layer is not None:
          query = self.projector(query)
          fragment = self.projector(fragment)


        frag_self_att = torch.stack([self.self_att_layer[i](fragment[:, i]) for i in range(self.n_way)], dim = 1)  

        frag_self_att= frag_self_att.squeeze(-1)        # batch x 2 x 5 x seq_len 

        # normalize attention score
        frag_self_att = torch.exp(frag_self_att)*fragment_mask   # batch x 2 x 5 x seq_len
        frag_self_att = frag_self_att/(frag_self_att.sum(axis = -1, keepdims = True) + 1e-7)  # batch x 2 x 5 x seq_len

        # add dropout
        if self.dropout_rate>0:
          frag_self_att = self.dropout(frag_self_att)

        # weighted sum
        frag_code = fragment * frag_self_att.unsqueeze(-1)  # batch x 2 x 5 x seq_len x frag_latent_dim
        frag_code = frag_code.sum(axis = -2)          # batch x 2 x 5 x frag_latent_dim

    
        fragment_reshape = fragment.view(fragment.size(0), -1, *fragment.size()[3:])  # batch x 10 x seq_len x frag_latent_dim
        query_reshape = query.unsqueeze(1)  # batch x 1 x seq_len x frag_latent_dim

        q_att =(self.query_att(query_reshape)) #batch x 1 x seq_len x value_dim
        f_att = (self.frag_att(fragment_reshape))  # batch x 10 x seq_len x value_dim
        
        # reshape and broadcast: batch x 1 x 1 x seq_len x frag_latent_dim, batch x 10 x seq_len x 1 x frag_latent_dim
        qf_att = (self.query_frag_att((query_reshape.unsqueeze(-3))*(fragment_reshape.unsqueeze(-2))))     # batch x 10 x seq_len x seq_len  x value_dim
        qf_att = q_att.unsqueeze(-3) + f_att.unsqueeze(-2) + qf_att   # batch x 10 x seq_len x seq_len x value_dim

        # max along column 
        qf_att,_ = torch.max(qf_att, dim =-3)   # batch x 10 x seq_len x value_dim
        
        qf_gate = torch.sigmoid(self.value_gate(qf_att).squeeze(-1)) * query_mask.unsqueeze(1)  #batch x 10 x seq_len

        qf_att_normalized = torch.exp(self.value_att(qf_att).squeeze(-1)) * query_mask.unsqueeze(1)
        qf_att_normalized = qf_att_normalized / (qf_att_normalized.sum(dim = -1, keepdims=True) + 1e-7)
        
        # add dropout
        if self.dropout_rate > 0:
          qf_att_normalized = self.dropout(qf_att_normalized)

        query_code = (query_reshape * qf_att_normalized.unsqueeze(-1)).sum(axis = 2) # batch x 10 x frag_latent_dim
        query_code = query_code.view(frag_code.size())  # batch x 2 x 5 x frag_latent_dim
        
        return frag_code, query_code, frag_self_att, qf_gate,  query


class Text_Encoder(nn.Module):

    # define all the layers used in model
  def __init__(self, 
               emb_dim: int = 100, 
               seq_len: int = 100, 
               num_filters: int = 20, 
               kernel_sizes: List[int] = [1,3,5],
               text_projection_layer: str = 'linear', 
               text_hidden_dim: int = 100,
               dropout_rate: float = 0.5):
      
        super().__init__()
        self.emb_dim = emb_dim
        self.seq_len = seq_len
        self.num_filters = num_filters
        self.kernel_sizes = kernel_sizes
        self.text_projection_layer = text_projection_layer
        
        # user projector
        if text_projection_layer is not None:
          self.projector = Emb_Projection(layer_name = text_projection_layer, 
                                          emb_dim= emb_dim, 
                                          hidden_dim = text_hidden_dim)
          self.emb_dim = self.projector.output_dim    
        else:
           self.projector = None
        
        # CNN layer
        self.base_convs = nn.ModuleList([nn.Conv1d(self.emb_dim, self.num_filters, f) for f in self.kernel_sizes])
        
        self.dropout = nn.Dropout(p=dropout_rate)

  def forward(self, x):
        
        if self.text_projection_layer is not None:
          x = self.projector(x)

        x = torch.swapaxes(x, 1, 2)
        z_base = [F.relu(conv(x)) for i,conv in enumerate(self.base_convs)]  # output of three conv
        
        z_base = [F.max_pool1d(i, i.size(2)).squeeze(2) for i in z_base] 
        z = torch.cat(z_base, 1)  # N, len(filter_sizes)* num_filters
        z = self.dropout(z)  # N, len(filter_sizes)* num_filters
        
        return z

# projection by LSTM or linear
class Emb_Projection(nn.Module):

  '''Project a tensor by LSTM or linear'''

  def __init__(self, 
               layer_name: str = 'linear', 
               emb_dim: int = 100, 
               hidden_dim: int = 100):
    
    super().__init__()
    self.layer_name = layer_name
    self.emb_dim = emb_dim
    self.hidden_dim = hidden_dim

    if self.layer_name == 'lstm':
      
      self.projection_layer = nn.LSTM(emb_dim, hidden_dim,
                           num_layers=1, bidirectional=True,
                           bias = False, batch_first=True)
      
      self.output_dim = 2 * self.hidden_dim
      
    elif self.layer_name == 'linear':
      self.projection_layer = nn.Linear(emb_dim, hidden_dim)
      self.output_dim = self.hidden_dim
      
  # x can be in any size, -1 is the emb size, -2 is seq length
  def forward(self, x):
    
    seq_len = x.size(-2)
    emb_dim = x.size(-1)
    input_size = x.size()

    if self.layer_name == 'lstm':
      x = x.view(-1, seq_len, emb_dim)
      x_mask = 1 - torch.all(x==0, dim = -1, keepdims = True).float()
      
      x,_ = self.projection_layer(x)  
      #x = torch.swapaxes(self.bn(torch.swapaxes(x, 1, 2)),1,2) 
      x = x * x_mask 
      x = x.view(*input_size[0: len(input_size)-1], -1)      
    else:
      x = self.projection_layer(x)  
      x_mask = 1 - torch.all(x==0, dim = -1, keepdims = True).float()
      x = x * x_mask

    return x

class FastSR(nn.Module):
  def __init__(self, 
               args,                  # model configuration     
               encoder,               # sentence encoder
               frag_encoder = None,   # fragment encoder
               context_encoder = None # context encoder
               ):

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
    self.initial_weights = args.initial_weights
    
    if self.use_fragment:
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
      
    elif metric=='cosine':     
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
  # Tagging using L2 distance
  def seq_tagging_l2(self, 
                     frag_code,       # Encoded fragments
                     query,           # Encoded query sentences
                     query_mask       # Mask for padding symbols
                     ): 
        
        """Tagging based on L2 distance between prototypes and word embeddings"""

        # get fragment prototype
        frag_proto = frag_code.mean(dim = -2)   #  batch x 2  x frag_latent_dim

        query = query * query_mask.unsqueeze(-1)
        
        # calculate L2 distance, shape: -1  x  seq_len x 2
        distance = torch.pow(frag_proto.unsqueeze(1) - query.unsqueeze(2), 2).sum(-1)

        tags = torch.softmax( -distance, dim = -1)  # shape -1  x  seq_len x 2
        tags = tags * query_mask.unsqueeze(-1)
        
        return tags
    
    
  
  def forward(self, 
              x_support_set,        # A dictionary with all support data components: sentence, fragment, and context
              x_query_set = None,   # A dictionary with all query data components: sentence, fragment, and context
              y_query=None,         # label of query
              return_loss: bool = True,   # whether to return loss
              return_att: bool = False,   # whether to return attention score
              return_tag: bool = False    # whether to return tags
              ):
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

    # encoding by CNN
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
    
    
    # normalize the weights
    component_weight_norm = torch.softmax(self.component_weights, dim = -1).view(-1)
    component_weight_norm = {item: component_weight_norm[i] for i, item in enumerate(self.components)}
       
    sim = component_weight_norm["semantics"] * sim
    
    if self.use_fragment:
        
        frag_code, query_code, frag_att, query_att, query = self.frag_encoder(x_query, fragment, query_mask, fragment_mask)
        
        query_att = query_att.view(batch_size, n_way, k_shot, -1)
        
        # take average of k-shot
        query_att = torch.swapaxes(query_att.mean(2), 1,2)     # batch x seq_len x n_way  
        
        # multitask learning, get tagging cost
        if self.tagging:        
            tag = self.seq_tagging_l2(frag_code, query, query_mask)  # use L2 distance, batch x seq_len x n_way
            
            # tag probility x query attention
            tag = tag * query_att
          
            tag = tag[:,:, -1]

        frag_code = frag_code.mean(dim=2)  # batch x 2  x frag_latent_dim
        query_code = query_code.mean(dim = 2)     # batch x 2 x frag_latent_dim
        z_dim = frag_code.size(-1)
        frag_sim = - torch.pow(frag_code - query_code, 2).sum(-1)/math.sqrt(z_dim)

        sim += component_weight_norm["fragment"]*frag_sim

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
      
        criteria = nn.BCELoss(reduction = 'none')

        loss = criteria(p_y[:, 1], y_query)  
        loss =  loss.mean()

        returned_items["query_loss"] = loss
    
        if self.tagging:

            if self.syn_cost:                      # add regularization term in the total cost
              
              # max tag prob as a pseduo prob. for sentence calssification
              max_tag_prob, _ = tag.max(dim = -1)
              reg_loss = criteria(p_y[:, 1], max_tag_prob)  
              
              tag_loss = criteria(tag * p_y[:, 1].unsqueeze(-1), y_tag)
              tag_loss = (tag_loss.sum(-1)/(query_mask.sum(-1) + 1e-7))
              
              tag_loss = reg_loss + tag_loss
              
            else:
              tag_loss = criteria(tag, y_tag)
              tag_loss = (tag_loss.sum(-1)/(query_mask.sum(-1) + 1e-7))
            
            tag_loss = tag_loss.mean()

            returned_items["query_loss"] = loss
            
            loss = (1-self.tag_cost_weight) * loss + self.tag_cost_weight * tag_loss
            returned_items["tag_loss"] = tag_loss
            
        returned_items["loss"] = loss

    if return_att:
        
        returned_items["frag_att"] = frag_att.detach().cpu().numpy() 
        returned_items["query_att"] = query_att.detach().cpu().numpy()
   
    if return_tag:
      
        returned_items["tag_label"] = y_tag
        returned_items["tag"] = tag
        returned_items["frag_proto"] = frag_code
        returned_items["query"] = query
        returned_items["query_mask"] = query_mask
        
    return returned_items

