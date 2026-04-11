# FastSR

## Overview

This repository contains code implementing FastSR framework, a few-shot based deep learning solution to automate medical evidence extraction in high-expertise, low-label environment. The details of our algorithm are described in our paper: <br> 
<i>Automating in High-expertise, Low-label Environments: Evidence-based Medicine by Expert-Augmented Few-shot Learning</i>


## Setup
### Prerequisites

    Python 3.8+
    Required Python packages listed in requirements.txt

### Installation

Clone the repository:

    git clone https://github.com/rul110/FastSR.git
    cd FastSR

Create and activate a virtual environment (optional but recommended):

    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

Install the required packages:

    pip install -r requirements.txt

## Datasets and Preprocessing
We used three datasets:
- EBM: A description of data format can be found at "data/EBM/data_format.csv". Folder "data/EBM/train/200/0/train_sentence.csv" contains 200 sentences sampled from <a href="https://github.com/bepnye/EBM-NLP">EBM-NLP</a> dataset. "data/EBM/test/test_sentence_expert.csv" contains a few testing sentences from EBM-NLP dataset. 
- WD: Our proprietary dataset for Wilson disease can be shared unpon request. A description of data format can be found at "data/WD/data_format.csv". "data/WD/train/train_sentences.csv" contains a few sample sentences.
- COVID: Our proprietary dataset for COVID can be shared unpon request. A description of data format can be found at "data/COVID/data_format.csv". "data/COVID/train/train_sentences.csv" contains a few sample sentences.


The training and testing datasets need to be preprocessed to extract sentence semantics, global context, and fragment representations. 
- Check Jupyter Notebook <a href="preprocess/data_preprocessing.ipynb">preprocess/data_preprocessing.ipynb</a> for the processing steps and code. Please refer to <a href="data/EBM/data_full.tar.gz"> data/EBM/data_full.tar.gz</a> for the list of features generated for model training and testing.
- For global contexts, a trained model can be found at <a href="preprocess/section_model.tar.gz"> section_model.tar.gz </a>. This model is used by data_preprocessing.ipynb to generate a global context for each sentence. 


## Model Configurations

All model parameters shoud be saved into a json file. A few examples can be found in "config" folder. For example, "full.json" contains model parameters used to train a full model using EBM-NLP dataset. Another configuration file, "full_minus_context.json" specifies the abation model where our global context module is removed. Note, since EBM dataset only contains sentences from abstracts, the global context module is disabled.

## Usage
    cd FastSR
    python src/run.py config/full.json 

The trained model, predictions, and performance metrics are placed into an output folders as defined in the configuration json file.

## Performance reporting
To generate performance report, check Jupyter Notebook <a href="output/performance_report.ipynb">output/performance_report.ipynb</a> for the code to generate performance metrics, precision@3, recall@3, F1@3, and PRC, for both classificaiton and tagging tasks as shown in the paper.

