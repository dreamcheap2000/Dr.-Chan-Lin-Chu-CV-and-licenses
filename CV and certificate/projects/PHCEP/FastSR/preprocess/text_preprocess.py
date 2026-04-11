import numpy as np
import pandas as pd
from sklearn.utils import shuffle
import torch
import pickle
import re
import spacy
from word2number import w2n
from tika import parser
import os
from sklearn.preprocessing import MultiLabelBinarizer
import ast

from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

punkt_param = PunktParameters()
abbreviation = ['fig', 'e.g', 'u.s', 'etc', 'i.e', 'univ', 'u.s.a', 'u.k', 'al','inc', 'no', 'vs', 'govt']
punkt_param.abbrev_types = set(abbreviation)
sent_tokenize = PunktSentenceTokenizer(punkt_param)


class Text_Processor():
    
    def __init__(self, sent_len, max_words_per_sec, max_sent_per_sec, \
                        sent_len_per_sec, emb_dim):
        
        self.sent_len = sent_len
        self.max_words_per_sec = max_words_per_sec
        self.max_sent_per_sec = max_sent_per_sec
        self.sent_len_per_sec = sent_len_per_sec
        self.emb_dim = emb_dim
        
        self.COLUMNS = ["Perspective",
                        #"Study Design",
                        "Data Source", 
                        "Study Period",
                        "Country",
                        'Sample Size',
                        'Population',
                        'Intervention',
                        'Negative'
                       ]
        
       
            
        self.nlp = spacy.load('en_core_web_sm')
        #https://github.com/explosion/spaCy/blob/master/spacy/glossary.py
        self.POS_GLOSSARY = ['ADJ','ADP','ADV','CCONJ','DET','INTJ','NOUN',\
                        'NUM','PART','PRON','PROPN','SYM','VERB','X']

        self.ENT_GLOSSARY = ["PERSON","NORP", "FACILITY",\
                        "FAC","ORG", "GPE", "LOC", "PRODUCT",\
                        "EVENT","WORK_OF_ART", "LAW", "LANGUAGE",\
                        "DATE", "TIME", "PERCENT", "MONEY", "QUANTITY",\
                        "ORDINAL","CARDINAL"]

        self.IOB_GLOSSARY =['I','O','B']

        self.mlb = MultiLabelBinarizer()
        self.mlb.fit([[x] for x in self.POS_GLOSSARY + self.ENT_GLOSSARY + self.IOB_GLOSSARY + ['LIKE_NUM', 'PUNCT']])

        self.number = {
            'zero': 0,
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5,
            'six': 6,
            'seven': 7,
            'eight': 8,
            'nine': 9,
            'ten': 10,
            'eleven': 11,
            'twelve': 12,
            'thirteen': 13,
            'fourteen': 14,
            'fifteen': 15,
            'sixteen': 16,
            'seventeen': 17,
            'eighteen': 18,
            'nineteen': 19,
            'twenty': 20,
            'thirty': 30,
            'forty': 40,
            'fifty': 50,
            'sixty': 60,
            'seventy': 70,
            'eighty': 80,
            'ninety': 90,
            'hundred': 100,
            'thousand': 1000,
            'million': 1000000,
            'billion': 1000000000,
            'point': '.'
        }

        self.match_num = '^[0-9]+$'
        
        self.SECTION_LABEL = {0: 'introduction', \
                              1: 'results and discussion', \
                              2: 'conclusion', \
                              3: 'methods', \
                              4: 'case report', \
                              5: 'sponsorship, conflicts of interest, disclosure, acknowledgement', \
                              6: 'supplementary material', \
                              7: 'limitations', \
                              8: 'objectives', \
                              9: 'abbreviations', \
                              10: 'experimental section', \
                              11: 'figures and tables', \
                              12: 'measures'}



    # clean up text

    def normalize_string(self, s):
        s = re.sub(r'–', r'-', s)
        s = re.sub(r'[-]\s', r'-', s)
        s = re.sub(r'\?\x80\?s', r"'s", s)
        s = re.sub(r'\?\x80\?', r"-", s)
        s = re.sub(r'`', r"'", s)       
        s = re.sub(r'\s+', r' ', s)

        if len(s)==0:
            return s
        
        # remove sentences with email address and URL
        if re.search(r'[\w\.-]+@|http:+', s):
            return ''

        # remove sentences with more than half of digit or decimal or other number format - this will help remove table data
        if len(re.findall(r"[+-]?((\d+(\.\d*)?)|\.\d+)([eE][+-]?[0-9]+)?", s))/len(s.split()) > 0.5:
            return ''

        # remove sentences represent copy right or article history
        if 'reprint' in s.lower() or 'article history' in s:
            return ''
        
         # remove sentences represent copy right or article history
        if 'received' in s.lower() and \
            'accepted' in s.lower() and \
            'published' in s.lower():
            return ''
        
         # remove conflict of interest and some variates
        s1 = re.sub(r'\s+', '',s.lower())
        if 'conflictofinterest' in s1 or 'conflictsofinterest' in s1:
            return ''
        
         # remove Unauthorized reproduction and some variates
        s1 = re.sub(r'\s+', '',s.lower())
        if 'unauthorizedreproduction' in s1:
            return ''
        
        #####################################
        
        return s

    # if a block has  more than one third of proper cased words
    # most likely it's author information or references
    def is_author_info(self, s):
        s = s.strip()
        word_in_s = re.findall(r'[a-zA-Z]+', s)
        result = False
        
        if len(word_in_s)>0:
            # first word contains Capitals (sometimes the superscript can be a part of the first word)
            if len(re.findall(r"\b[A-Z][a-z]+", s))/len(word_in_s) > 0.6 and re.match(r'\w*[A-Z]', word_in_s[0]):
                 result = True
                    
        return result
       
    
    # Tokenize a sentence
    def tokenizer(self, s):
        
        tokens = self.nlp(s)    
        clean_tokens = []
        syntax = []
        annotations = []

        for t in tokens:
            
            syntax.append([t.ent_type_ if t.ent_type_ in self.ENT_GLOSSARY else '',\
                               t.ent_iob_ if t.ent_iob_  in self.IOB_GLOSSARY else '', \
                               'LIKE_NUM' if t.like_num else '', \
                               t.pos_ if t.pos_  in self.POS_GLOSSARY else '',\
                               'PUNCT' if t.is_punct else ''])
            
            annotations.append({"start": t.idx, \
                                 "end": t.idx + len(t.text),\
                                 "text": t.text})
            if not t.is_punct:
                
                token = t.lemma_      
                if t.lemma_=='-PRON-':
                    token = t.text

                if len(token)>0:       
                    # remove punct within a token
                    ts = re.findall(r'\w+', token) 

                    if len(ts)>0:  
                        clean_ts = []

                        for s in ts:
                            if s in self.number:
                                s = w2n.word_to_num(s)      
                            clean_ts.append(str(s))

                        clean_tokens += clean_ts

        count = 0
        for i in clean_tokens:
            if re.search(self.match_num, i):
                count+=1

        if count != len(clean_tokens):

            syntax = self.mlb.transform(syntax)

            return clean_tokens, syntax, annotations
        else:
            return [],[],[]   
   
    def find_neighbor_vectors(self, idx, s, glove_model, window):
        cnt = 0
        current = max(0, idx-window if idx==len(s)-1 else idx-int(window/2) )
        words=[]
        v = []
        vector = np.zeros(self.emb_dim)
        
        while cnt<window and current<len(s)-1:
            if glove_model.has_index_for(str(s[current])):
                v.append(glove_model.get_vector(str(s[current])))
                words.append(s[current])
                cnt += 1
            current +=1
        
        if len(v)>0:
            vector = np.array(v).mean(axis =0)
        
        return vector

    # vectorize each word in sentence
    def vectorize(self, sents, max_words_per_sent, glove_model):
        m = np.zeros((len(sents), max_words_per_sent, self.emb_dim))

        found_words = []
        not_found_words = []

        for i,s in enumerate(sents):
            for j, t in enumerate(s):
                if j < max_words_per_sent:

                    if glove_model.has_index_for(t):
                    #if t in glove_model.wv:
                        m[i, j] = glove_model.get_vector(t)
                        #m[i, j] = glove_model.wv[t]
                        if t not in found_words:
                            found_words.append(t)
                    
                    #elif t.lower() in glove_model.wv:
                    elif glove_model.has_index_for(t.lower()):
                        m[i, j] = glove_model.get_vector(t.lower())
                        if t.lower() not in found_words:
                            found_words.append(t.lower())
                    else:  
                        m[i, j] = self.find_neighbor_vectors(j, s, glove_model, 4)
                        
                        if str(t) not in not_found_words:
                            not_found_words.append(t)  

        return m, found_words, not_found_words
    
    # Vectorize syntax list
    def vectorize_syn(self, syn_list):
        
        syn_vector = np.zeros((len(syn_list), self.sent_len, len(self.mlb.classes_)))

        for i in range(len(syn_list)):
            syn = syn_list[i]  # an array
            l = min(self.sent_len, len(syn))
            syn_vector[i][0: l] = syn[0:l]
            
        return syn_vector


    def get_bert_emb_and_alignment(self, sentences, tokenizer, bert_model, annotations, device, max_length = 100, batch_size = 100):

      input_ids = []
      attention_masks = []
      alignments = []

      # For every sentence...
      for sent, annotation in zip(sentences, annotations):
      # `encode_plus` will:
      #   (1) Tokenize the sentence.
      #   (2) Prepend the `[CLS]` token to the start.
      #   (3) Append the `[SEP]` token to the end.
      #   (4) Map tokens to their IDs.
      #   (5) Pad or truncate the sentence to `max_length`
      #   (6) Create attention masks for [PAD] tokens.

          tokenized_batch : BatchEncoding = tokenizer(sent, truncation=True,
                              add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                              max_length = max_length,           # Pad & truncate all sentences.
                              #pad_to_max_length = True,
                              padding ='max_length',
                              return_attention_mask = True,   # Construct attn. masks.
                              return_tensors = 'pt')
          
          # Add the encoded sentence to the list.    
          input_ids.append(tokenized_batch['input_ids'])
      
          # And its attention mask (simply differentiates padding from non-padding).
          attention_masks.append(tokenized_batch['attention_mask'])

          # align tokens by annotations
          tokenized_text :Encoding  =tokenized_batch[0]
          tokens = tokenized_text.tokens

          alignment = {}

          for tid, anno in enumerate(annotation):
            for idx in range(anno["start"], anno["end"]):
              token_id = tokenized_text.char_to_token(idx)
              if token_id is not None:
                alignment[token_id]=(tid, anno["text"], tokens[token_id])
          
          alignments.append(alignment)
      
      # Convert the lists into tensors.
      input_ids = torch.cat(input_ids, dim=0)
      attention_masks = torch.cat(attention_masks, dim = 0)
    
      token_embeddings = []
      bert_model.eval()
      with torch.no_grad():
        for batch in range(0, len(input_ids), batch_size):
          outputs = bert_model(input_ids[batch: (batch + batch_size)].to(device), 
                               attention_masks[batch: (batch + batch_size)].to(device))   
          if len(outputs) > 2:
              hidden_states = outputs[2]
          else:
              hidden_states = outputs[1]    # some token classification bert model has two outputs only
                
          hidden_states = torch.stack(hidden_states[-4:], dim=-1).mean(dim = -1)
          token_embeddings.append(hidden_states.cpu())

      # get the last four layers
      token_embeddings = torch.cat(token_embeddings, dim=0) 

      return token_embeddings, alignments,attention_masks.numpy()

    def get_bert_emb(self, sentences, tokenizer, bert_model, device, max_length = 100):

      input_ids = []
      attention_masks = []

      # For every sentence...
      for sent in sentences:
      # `encode_plus` will:
      #   (1) Tokenize the sentence.
      #   (2) Prepend the `[CLS]` token to the start.
      #   (3) Append the `[SEP]` token to the end.
      #   (4) Map tokens to their IDs.
      #   (5) Pad or truncate the sentence to `max_length`
      #   (6) Create attention masks for [PAD] tokens.

          tokenized_batch : BatchEncoding = tokenizer(sent, truncation=True,
                              add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                              max_length = max_length,           # Pad & truncate all sentences.
                              pad_to_max_length = True,
                              return_attention_mask = True,   # Construct attn. masks.
                              return_tensors = 'pt')
          
          # Add the encoded sentence to the list.    
          input_ids.append(tokenized_batch['input_ids'])
      
          # And its attention mask (simply differentiates padding from non-padding).
          attention_masks.append(tokenized_batch['attention_mask'])

      
      # Convert the lists into tensors.
      input_ids = torch.cat(input_ids, dim=0)
      #print(input_ids.size())
      attention_masks = torch.cat(attention_masks, dim = 0)
      #print(attention_masks.size())

      bert_model.eval()
      with torch.no_grad():

          outputs = bert_model(input_ids.to(device), attention_masks.to(device))   
          if len(outputs) > 2:
              hidden_states = outputs[2]
          else: 
              hidden_states = outputs[1]  # some token classification model only returns 2 outputs

      # get the last four layers
      token_embeddings = torch.stack(hidden_states[-4:], dim=0) 

      # permute axis
      token_embeddings = token_embeddings.permute(1,2,0,3)

      # take the mean of the last 4 layers
      token_embeddings = token_embeddings.mean(axis=2).cpu().numpy()

      return token_embeddings,attention_masks.cpu().numpy()

    # process section

    def process_section_bert(self, section, tokenizer, bert_model, device, sent_len=40, max_sent = 20, emb_size = 768):

      # sent tokenization
      sents = sent_tokenize.tokenize(section)
 
      # initialize emb
      sec_emb = np.zeros((max_sent, sent_len, emb_size))

      # limit to max_sent
      l = min(len(sents), max_sent)

      if l>0:
        # get bert emb
        emb,_ = self.get_bert_emb(sents[0: l], tokenizer, bert_model, device, max_length = sent_len)
        sec_emb[0:l] = emb

      return sec_emb 


    def process_section(self, section, glove_model):

        words = 0
        truncted_sec = []
        sec_wv = None

        sents = sent_tokenize.tokenize(section)
        
        for s in sents:

            if len(truncted_sec) < self.max_sent_per_sec:  # control max # of sentences

                tokens, _, _ = self.tokenizer(s)

                if len(tokens)>2:   # a sentence has at least 3 words

                    words += len(tokens)

                    if words < self.max_words_per_sec:   # the total section cannot exceed the word limit

                        truncted_sec.append(tokens)

                    else:
                        truncted_sec.append(tokens)
                        break

            else:
                break
        
        #print(truncted_sec)
        # convert to word vectors
        if len(truncted_sec) > 0:

            sec_wv = np.zeros((self.max_sent_per_sec, self.sent_len_per_sec, self.emb_dim))

            wv, _, not_found_words = self.vectorize(truncted_sec, self.sent_len_per_sec, glove_model)

            sec_wv[0:len(wv)] = wv


        return sec_wv
    


     # generate all feature vectors from a dataframe with columns "sent","paragraph"
    def generate_bert_feature_from_sentences(self, df, tokenizer, bert_model, section_model = None, device=None):

        import time  
        start = time.time()  

        sents = []
        sent_syn = []
        token_sents = []
        section_prob = []
        #annotations = []
        wordvec = []
        alignment = []
        masks = []
        #section_encoding = []
        #other_features = []

        for idx, row in df.iterrows():

            if idx%50==0:
              print("start sentence {0} @ {1:.2f}".format(idx, time.time()-start))

            s = str(row["sent"]).strip()
            s = self.normalize_string(s)
            if len(s)<1:
                continue

            tokens, syn, annotation = self.tokenizer(s)

            sents.append(s)
            token_sents.append(tokens)
            sent_syn.append(syn)

            if section_model is not None:

                section = str(row["paragraph"]).strip()
                
                if section == None or len(section) < 5:
                    section = s
                    print(idx, 'missing context text here')
                
                sec_wv =  self.process_section_bert(section, tokenizer, bert_model, device, sent_len=self.sent_len_per_sec, max_sent = self.max_sent_per_sec, emb_size = self.emb_dim)
                prob = section_model.predict(sec_wv[None,:])
                section_prob.append(prob.reshape(-1))

            w, a, m = self.get_bert_emb_and_alignment([s], tokenizer, bert_model, [annotation], device, max_length = self.sent_len)
            wordvec.append(w)
            alignment += a
            masks.append(m.squeeze())

        wordvec = np.concatenate(wordvec, axis = 0)  
        
        print("start syntax @ {0:.2f}".format(time.time()-start))

        syn_vector = self.vectorize_syn(sent_syn)

        # align syntax 
        new_syntax = np.zeros_like(syn_vector)
        for idx, align in enumerate(alignment):
          for token_id in align:
            syn_id = align[token_id][0]
            new_syntax[idx][token_id] = syn_vector[idx][syn_id]

        section_prob = np.array(section_prob)
        masks = np.array(masks)

        all_features = {"wordvector": wordvec, \
                        "mask": masks,
                       "syntax":new_syntax, 
                       "section_prob": section_prob, \
                       "sentences": sents,\
                       "tokened_sentences": alignment}
        
        print("sentences: ", len(all_features["sentences"]))
        print("tokened_sentences: ", len(all_features["tokened_sentences"]))      
        print("features: ")
        print([(key, item.shape) for key,item in all_features.items() \
               if key not in ["sentences","tokened_sentences"]])    
        
        return all_features       
    
    # generate all feature vectors from a dataframe with columns "sent","paragraph"
    def generate_feature_from_sentences(self, df, glove_model, section_model):
        
        sents = []
        sent_syn = []
        token_sents = []
        section_prob = []
        section_encoding = []
        other_features = []

        for idx, row in df.iterrows():

            s = str(row["sent"]).strip()
            s = self.normalize_string(s)
            if len(s)<1:
                continue

            section = str(row["paragraph"]).strip()

            tokens, syn, _ = self.tokenizer(s)

            sents.append(s)
            token_sents.append(tokens)
            sent_syn.append(syn)

            if section == None or len(section) < 5:
                section = s
                print(idx, 'missing context text here')

            sec_wv = self.process_section(section, glove_model)
            
            x, lstm_code = section_model.predict(sec_wv[None,:])

            section_prob.append(x[0])
            section_encoding.append(lstm_code[0])

             # number of like_num tokens
            num_index = self.mlb.classes_.tolist().index('LIKE_NUM')
            nums = syn[:,num_index].sum()

            normed_len = min(1, len(tokens)/self.sent_len)
            normed_nums = nums/len(tokens)

            other_features.append([len(tokens), nums])

        wordvec, f, nf = self.vectorize(token_sents, 100, glove_model)
        print(nf)

        syn_vector = self.vectorize_syn(sent_syn)
        section_prob = np.array(section_prob)
        section_encoding = np.array(section_encoding)
        other_features = np.array(other_features)

        all_features = {"wordvector": wordvec, \
                       "syntax":syn_vector, 
                       "section_prob": section_prob, \
                       "section_encoding": section_encoding, \
                       "other_features": other_features,\
                       "sentences": sents,\
                       "tokened_sentences": token_sents}
        
        print("sentences: ", len(all_features["sentences"]))
        print("tokened_sentences: ", len(all_features["tokened_sentences"]))      
        print("features: ")
        print([item.shape for key,item in all_features.items() \
               if key not in ["sentences","tokened_sentences"]])    
        
        return all_features



    def parse_pdf(self, filename):
    
        text = ""
        try:
            pdf = parser.from_file(filename)
            if "content" in pdf:
                if pdf["content"] != None:
                    text = pdf["content"]
                    
                    # remove line number #
                    lines = re.findall("\w+\s*\n", text)
                    num1 = re.findall(r"\w+\d+\s*\n", text)
                    num2 = re.findall(r"\n\s*\d+\w+", text)
                    
                    if max(len(num1), len(num2))>= 0.5 * len(lines):
                        if len(num1)>len(num2):
                            text = re.sub(r"\d+\s*\n", " \n", text)
                        else:
                            text = re.sub(r"\n\s*\d+", "\n ", text)
                            
                    if max(len(num1), len(num2))< 0.5 * len(lines) and max(len(num1), len(num2))>= 0.1 * len(lines):
                        print("Warning: it seems the text contains line number, but not sufficient enough to be removed. Check")
                            
                else:
                    print(filename, " cannot be parsed; No content extracted")
                    text = ''
        except:
            print(filename, " cannot be parsed")
            text = ''
            pass
        
        return text
    
    
    def parse_paragraph(self, p, min_words=5):
    
        p = self.normalize_string(p)

        sents = sent_tokenize.tokenize(p)

        cleaned_sents=[]
        for s in sents:

            if len(re.findall(r"[a-zA-Z]+", s)) < min_words:   # sentence is all numbers
                continue
            # remove sentences with more than half of digit or decimal or other number format - this will help remove table data
            if len(re.findall(r"[+-]?((\d+(\.\d*)?)|\.\d+)([eE][+-]?[0-9]+)?", s))/len(s.split()) > 0.5:
                continue
            
                
            if len(re.findall(r"\w\w+", s)) >= min_words:

                cleaned_sents.append(s)

        return cleaned_sents
    
    
    def parse_raw_text(self, text, filename, min_para_len=5, min_sent_len=5):

        result = pd.DataFrame([], columns=["sent","paragraph"])

        # first segment into paragraphs \n\n
        blocks = re.split(r"\n\n", text)
        
        if 'REFERENCES' in blocks:
            ref_index=blocks.index('REFERENCES')
            blocks=blocks[:ref_index]
        elif 'References' in blocks:
            ref_index=blocks.index('References')
            blocks=blocks[:ref_index]
        elif 'references' in blocks:
            ref_index=blocks.index('references')
            blocks=blocks[:ref_index]

        if 'DISCUSSION' in blocks:
            ref_index=blocks.index('DISCUSSION')
            blocks=blocks[:ref_index]
        elif 'Discussion' in blocks:
            ref_index=blocks.index('Discussion')
            blocks=blocks[:ref_index]
        elif 'discussion' in blocks:
            ref_index=blocks.index('discussion')
            blocks=blocks[:ref_index]

        # if only one block, switch to single \n as paragraph detector
        if len(blocks) == 1:
            print(filename + "paragraphs may not be segmented correctly!")

        curr = ''
        for i, b in enumerate(blocks):
        # In case of the paragraph is not devided by two newline
            if ('REFERENCES' in b[:12] or 'References' in b[:12] or 'references' in b[:12] or 
                'ACKNOWLEDGEMENTS' in b[:20] or 'acknowledgements' in b[:20] or 'Acknowledgements' in b[:20]):
                break
            
            b = b.strip()

            # replace URL starting from be begining
            b = re.sub(r'http(.+[/])+', ' ', b)

            # reploce doi:
            b = re.sub(r'doi:\S+', ' ', b)
            
            # replace "-\n" or –\n by ""
            b = re.sub(r'[-–]\s', r'', b)

            # replace "–"  by "-"
            b = re.sub(r'[–]', r'-', b)

            # remove line break    
            b = re.sub(r'\s+',' ', b.strip())

            # remove citation numbers since it interfere sentnece segmentation
            # remove the period to comma so that there won't be wrong cut
            b = re.sub(r'(\D)\.([\d\-–,;]+) ?([A-Z]?)', r'\1 [\2], \3',b)

            author_info = self.is_author_info(b)
            
            if author_info:
                b = b+". "  # Ensure this can be split as a sentence later
                
            # if Paragraph starts with upper case or it's author inforamation
            # leave it as a paragraph and don't concatenate  
            
            # skip the null block
            if len(b)==0:
                continue
                
            if b[0].isupper() or author_info:  
                
                
                if curr != []:  # there is something left from last block

                    sents = self.parse_paragraph(curr, min_sent_len)

                    if len(sents)>0:

                        sents_in_para=[(s, curr) for s in sents]
                        sents_in_para = pd.DataFrame(sents_in_para, \
                                                     columns=["sent","paragraph"])
                        #print(len(sents_in_para))

                        result = result.append(sents_in_para, ignore_index=True)
                        #print(len(result))  

                    curr = ''

            b = curr + ' '+ b.strip()  # add last block
            b = b.strip()

            if (b[-1] in ['.','!','?']) or (b[-2:] in ['."','!"','?"']):  # paragraph ends properly

                sents = self.parse_paragraph(b, min_sent_len)

                if len(sents)>0:

                    sents_in_para=[(s, b) for s in sents]
                    sents_in_para = pd.DataFrame(sents_in_para, \
                                                 columns=["sent","paragraph"])

                    result = result.append(sents_in_para, ignore_index=True)
                curr = ''

            else: 
                curr = b


        return result          


def get_fragment_mask(frag, frag_inds, sent, tokenizer,sent_len = 100):

  if frag is not None:

    tokenized_batch : BatchEncoding = tokenizer(sent, truncation=True,
                                add_special_tokens = True, # Add '[CLS]' and '[SEP]'
                                max_length = sent_len,           # Pad & truncate all sentences.
                                pad_to_max_length = True,
                                return_attention_mask = True,   # Construct attn. masks.
                                return_tensors = 'pt')
            
    tokenized_text :Encoding  =tokenized_batch[0]
    tokens = tokenized_text.tokens

    fs = frag.split(";")
    ids = ast.literal_eval(frag_inds)

    frag_tokens = []
    frag_tokens_ids = []

    for i, f in zip(ids, fs):
      
      for idx in range(int(i), int(i)+len(f)):
        token_id = tokenized_text.char_to_token(idx)
        if token_id is not None:
          if token_id not in frag_tokens_ids:
            frag_tokens_ids.append(token_id)
            frag_tokens.append(tokens[token_id])

    return frag_tokens,frag_tokens_ids

def train_val_split(df, label_cols, fold = 5):

    #splite train (2/3) and validation (1/3)
    frac = (fold - 1)/fold

    # sentence indexes for train 
    Train_pos_set ={}
    Train_neg_set ={}

    # sentence indexes for validation validation
    Val_pos_set ={}
    Val_neg_set ={}

    for name in label_cols:
      if name!='Negative':
          print("\n", name)

          # positive case
          x = df[df[name]==1][name].index.values
          x = shuffle(x, random_state=42)

          N = int(len(x)*frac)
          pos_train = x[0:N]  # Only sentence ids are stored
          pos_val = x[N:]
          
          print("pos_train", len(pos_train))
          print("pos_val", len(pos_val))
          
          # Negative case
          # double sample the cases for the other classes
          other_class = df[(df[name]==0) & (df["Negative"]==0)][name].index.values 
          neg = df[df["Negative"]==1][name].index.values  

          neg = np.concatenate([other_class, neg], axis = 0)
          
          neg = shuffle(neg, random_state=42)
          
          #split train and validation data in negative case
          N = int(len(neg)*frac)
          neg_train = neg[0:N]
          neg_val = neg[N:]
          print("neg_train", len(neg_train))
          print("neg_val", len(neg_val))
          
          # store the indexes into a diction
          Train_pos_set[name] = pos_train
          Train_neg_set[name] = neg_train

          Val_pos_set[name] = pos_val
          Val_neg_set[name] = neg_val
    
    return Train_pos_set, Train_neg_set, Val_pos_set, Val_neg_set

def get_tag(tokens):

    if len(tokens)>1:
        prev = tokens[-2]
    else:
        prev = 0
        
    cur = tokens[-1]
        
    if cur == 0:
        tag = 0  
    else:
        if prev == 0:
            tag = 1
        else:
            tag = 2
    
    return tag

def extract_all_features(sampled_train_df, label_cols,  data_folder, 
                     processor, tokenizer, bert_model, device, lower_labels = None,
                     num_negative_words = 5, split_data = True,
                     use_label_emb = False):
    
    # first save Y values
    for col in label_cols:
      sampled_train_df[col] = sampled_train_df[col].fillna(0)
      
    Y_values ={col: sampled_train_df[col].values for col in label_cols}
    pickle.dump(Y_values,open(os.path.join(data_folder, "sentence_labels.pkl"),'wb'))
    
    # vectors
    annotations = []
    sentences = sampled_train_df.text.values
    for s in sampled_train_df.text.values:
      tokens, syn, annotation = processor.tokenizer(s)

      annotations.append(annotation)
    
    token_embeddings, alignment, attention_masks = processor.get_bert_emb_and_alignment(sentences, tokenizer, bert_model, annotations, device, max_length = processor.sent_len)
    
    print(f"embedding size: {token_embeddings.shape}, mask size: {attention_masks.shape}")
    
    np.save(os.path.join(data_folder,  "wordvectors.npy"),token_embeddings)

    np.save(os.path.join(data_folder, "sentence_masks.npy"),attention_masks)
    
    pickle.dump(alignment, open(os.path.join(data_folder, "alignment.pkl"), 'wb'))
    
    # label embedding
    if use_label_emb:
        for label in label_cols:
          sampled_train_df[label + "_text"] = sampled_train_df.apply(lambda row: [col.replace("/Other",'') for col in sampled_train_df.columns if (row[col] ==1) and (row[label]==1) and label in col], axis = 1)
          sampled_train_df[label + "_text"] = sampled_train_df[label + "_text"].apply(lambda x: list(set(re.split(r'[./ ]',' '.join(x)))))

        # random sample three words for negative text
        sampled_train_df['Negative' + "_text"] = sampled_train_df.apply(lambda row: np.random.choice(np.array(row['text'].split()), num_negative_words).tolist() if row['Negative']==1 else [], axis = 1)

        label_encodings = {}

        for label in label_cols:
            print(f"============{label}=============")
            label_encodings[label] = np.zeros((len(sampled_train_df), 1, 768))
            sentences = sampled_train_df[sampled_train_df[label]==1][label + "_text"].apply(lambda x: ' '.join(x))
            print(sentences.head(5))
            emb, mask = processor.get_bert_emb(sentences.values, tokenizer, bert_model, device, max_length = 30) 
            print(emb.shape, mask.shape)
            emb = (emb * mask[:,:, None])
            for idx, i in zip(sentences.index.values, range(len(emb))):
                # remove the first and the last special token
                e = emb[i, 1: (mask[i].sum()-1),:].sum(axis = 0) / (mask[i].sum()-2) 
                label_encodings[label][idx] = e[None, :]

        pickle.dump(label_encodings, open(os.path.join(data_folder, "label_emb.pkl"), 'wb'))        
    
    # fragments

    all_frag_token_ids = {}
    all_frag_tokens = {}
    bio_tags = {}

    attention_masks = np.load(os.path.join(data_folder, "sentence_masks.npy"))
    
    
    for col in label_cols:
      
      # initial fragment contains all tokens
      # if a sentence does not belong to this class, the fragment consists of all tokens
      frag_token_ids = attention_masks.copy() # use a copy, otherwise attention_masks will be modified
      frag_tokens = [[]]*len(attention_masks)

      for idx, row in sampled_train_df[sampled_train_df[col]==1].iterrows():
          
          # reset mask to all zeros
          frag_token_ids[idx] = 0

          # combine all fragments

          for sub_label in lower_labels[col]:
              
            if not pd.isnull(row[sub_label+' Fragment']): 
                tokens,tokens_ids = get_fragment_mask(row[sub_label+' Fragment'], row[sub_label+'_fragment_index'], 
                              row['text'], tokenizer)
                
                # update the mask to only fragment
                frag_token_ids[idx][tokens_ids] = 1
                frag_tokens[idx] = frag_tokens[idx] + tokens
               
      all_frag_token_ids[col] = frag_token_ids
      all_frag_tokens[col] = frag_tokens
      
      # tags for traditional tagging
      
      bio_tags[col] = []
    
      for idx, seq in enumerate(all_frag_token_ids[col]):
          
          if all_frag_tokens[col][idx]!=[]: # contains fragment
              tags = np.array([get_tag(seq[0:i+1]) for i in range(len(seq))])            
          else:
              tags = np.zeros(len(seq))
              
          bio_tags[col].append(tags)
        
    pickle.dump(all_frag_token_ids, open(os.path.join(data_folder, "frag_token_ids.pkl"), 'wb'))
    pickle.dump(all_frag_tokens, open(os.path.join(data_folder, "frag_tokens.pkl"), 'wb'))  
    pickle.dump(bio_tags, open(os.path.join(data_folder, "sequence_tag.pkl"), 'wb'))  
    
    # train/eval split
    
    if split_data:
        Train_pos_set, Train_neg_set, Val_pos_set, Val_neg_set = train_val_split(sampled_train_df, label_cols, fold = 5)

        pickle.dump(Train_pos_set, open(os.path.join(data_folder, "train_pos_dict.pkl"),"wb"))
        pickle.dump(Val_pos_set, open(os.path.join(data_folder,"val_pos_dict.pkl"),"wb"))
        pickle.dump(Train_neg_set, open(os.path.join(data_folder,"train_neg_dict.pkl"),"wb"))
        pickle.dump(Val_neg_set, open(os.path.join(data_folder, "val_neg_dict.pkl"),"wb"))