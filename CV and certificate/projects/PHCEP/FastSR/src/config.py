import os
from typing import Union, List, Any, Dict

class ModelConfig():
    
    ''' All model configuration parameters '''
    
    def __init__(self, 
                 labels: Union[List[str], None] = ['participants', 'interventions','outcomes'],         # class label list
                 dist_metric: str = 'l2',   # distance measure
                 n_way: int = 2,            # number of classes
                 k_shot: int = 5,           # number of shots
                 train: bool = False,       # train mode or not
                 batch_size: int = 32,  
                 learning_rate: float = 1e-4, 
                 training_eposides: int  = 50, 
                 validation_eposides: int = 50,
                 epochs: int = 100, 
                 patience: int = 5,         # early stopping patience
                 save_model: bool = True, 
                 verbose: bool = True, 
                 update_step: int = 100, 
                 learning_rate_schedule: bool = True, 
                 gamma: float = 0.9, 
                 emb_dim: int = 200,        # word vector embedding dimension
                 seq_len: int = 100,       # sentence length
                 sentence_mask: bool = True,    # sentence with masked padding symbols
                 num_filters: int = 20,         # number of CNN filters
                 kernel_sizes: List[int] = [1,3,5], # CNN filter sizes
                 use_context: bool = False,     # whether to use global context
                 context_dim: int = 13,         # dimension of global context
                 context_latent_dim: int = 10,  # dimension of global context after transformation
                 use_fragment: bool = False,    # whether to use fragment
                 tagging: bool = False,         # whether to perform tagging
                 use_lstm: bool = False,        # whether to use LSTM layer in model
                 tag_cost_weight: float = 0.1,  # weight of fragment distances - Check this
                 initial_weights: List[float] = [2.0,1.0,1.0], # initial weight of semenatics, fragment, context
                 text_projection_layer: str = 'linear',  # project embedding layer to reduce dimension
                 text_hidden_dim: int = 100,             # dimension of projected layer
                 att_projection_layer: str = 'linear',   # project layer in attention to reduce dimension
                 att_hidden_dim: int = 100,              # dimension of projected layer in attention
                 att_value_dim: int = 50,                # dimension of value layer in attention
                 att_dropout_rate: float = 0.3,          # attention dropout rate
                 syn_cost: bool = True                  # whether to apply regularization term in total cost
                 ):

        # Few shot parameters
        self.labels = labels
        self.n_way = n_way
        self.train = train
        self.batch_size = batch_size
        self.k_shot = k_shot
        self.dist_metric = dist_metric

        # Training parameters
        self.learning_rate = learning_rate
        self.training_eposides = training_eposides
        self.validation_eposides = validation_eposides
        self.epochs = epochs
        self.update_step = update_step
        self.learning_rate_schedule=learning_rate_schedule
        self.gamma = gamma
        self.patience = patience
        self.save_model = save_model
        self.verbose = verbose

        # Input data parameters
        self.emb_dim = emb_dim
        self.seq_len = seq_len
        self.sentence_mask = sentence_mask     # mask indicates padding symbols

        # CNN paramaters
        self.num_filters = num_filters
        self.kernel_sizes = kernel_sizes

        # Context parameters
        self.use_context = use_context
        self.context_dim = context_dim
        self.context_latent_dim = context_latent_dim

        # Fragment and tagging parameters
        self.use_fragment = use_fragment
        self.tagging = tagging # whether to enable sequence tagging
        self.use_lstm = use_lstm # whether to use LSTM for projection. if no, linear projection
        self.tag_cost_weight = tag_cost_weight
        self.initial_weights = initial_weights

        # Projection layer parameter
        self.text_projection_layer = text_projection_layer       # lstm, linear, or None
        self.text_hidden_dim = text_hidden_dim

        self.att_projection_layer = att_projection_layer       # lstm, linear, or None
        self.att_hidden_dim = att_hidden_dim
        self.att_dropout_rate = att_dropout_rate
        self.att_value_dim = att_value_dim

        self.syn_cost = syn_cost         # continous, binary, none
        
    def set_option(self, key, value):
        self.__dict__[key] = value
  
    def print_options(self):
        for key in self.__dict__.keys():
          if not key.startswith("data"):
            print(f" {key}\t: \t{self.__dict__[key]}")

    def __setitem__(self, key: Any, value: Any):
        self._extra_attributes[key] = value

    def __getitem__(self, key: Any) -> Any:
        return self._extra_attributes[key]

    def convert_to_dict(self) -> Dict[Any, Any]:
        self._extra_attributes["labels"] = self.target_dim
        self._extra_attributes["dist_metric"] = self.dist_metric
        self._extra_attributes["n_way"] = self.n_way
        self._extra_attributes["k_shot"] = self.k_shot
        self._extra_attributes["train"] = self.train
        self._extra_attributes["batch_size"] = self.batch_size
        self._extra_attributes["learning_rate"] = self.learning_rate
        self._extra_attributes["training_eposides"] = self.training_eposides
        self._extra_attributes["validation_eposides"] = self.validation_eposides
        self._extra_attributes["epochs"] = self.epochs
        self._extra_attributes["patience"] = self.patience
        self._extra_attributes["save_model"] = self.save_model
        self._extra_attributes["verbose"] = self.verbose
        self._extra_attributes["update_step"] = self.update_step
        self._extra_attributes["learning_rate_schedule"] = self.learning_rate_schedule
        self._extra_attributes["gamma"] = self.gamma
        self._extra_attributes["emb_dim"] = self.emb_dim
        self._extra_attributes["seq_len"] = self.seq_len
        self._extra_attributes["sentence_mask"] = self.sentence_mask
        self._extra_attributes["num_filters"] = self.num_filters
        self._extra_attributes["kernel_sizes"] = self.kernel_sizes
        self._extra_attributes["use_context"] = self.use_context
        self._extra_attributes["context_dim"] = self.context_dim
        self._extra_attributes["context_latent_dim"] = self.context_latent_dim
        self._extra_attributes["use_fragment"] = self.use_fragment
        self._extra_attributes['tagging'] = self.tagging,
        self._extra_attributes['use_lstm'] = self.use_lstm
        self._extra_attributes['tag_cost_weight'] = self.tag_cost_weight
        self._extra_attributes["initial_weights"] = self.initial_weights
        self._extra_attributes["text_projection_layer"] = self.text_projection_layer
        self._extra_attributes["att_projection_layer"] = self.att_projection_layer
        self._extra_attributes["att_hidden_dim"] = self.att_hidden_dim
        self._extra_attributes["att_value_dim"] = self.att_value_dim
        self._extra_attributes["att_dropout_rate"] = self.att_dropout_rate
        self._extra_attributes["syn_cost"] = self.syn_cost

        return self._extra_attributes

    def save(self, save_root_path: str):
        data = {"model_config": self.convert_to_dict()}
        with open(os.path.join(save_root_path, "model_config.toml"), "w") as f:
            toml.dump(data, f)

    @classmethod
    def from_toml(cls, toml_path: str):
        with open(toml_path, "r") as f:
            data = toml.load(f)
        return cls(**data["model_config"])

    def __repr__(self):
        
        output_str = "model config: "
        config_dict = self.convert_to_dict()
        
        for key in config_dict:
            output_str = output_str + "\n" + key + ": \t" + config_dict[key]    
        
        return output_str
