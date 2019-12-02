# -*- coding: utf-8 -*-
"""code mixed.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XwtDhCMUxUiILBMur5DSjGxewR1dK_uI
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
import re

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np

import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('sentiwordnet')

from nltk.corpus import wordnet as wn
from nltk.corpus import sentiwordnet as swn
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, word_tokenize


def preprocess_data(data):
    for x in range (0, len(data)):

        data["Sentence"][x] = str(data["Sentence"][x])


        # Replace @name by USER
        data["Sentence"][x] = re.sub('@[\w\_]+', "USER", data["Sentence"][x])

        # Replace #name by HASHTAG
        data["Sentence"][x] = re.sub('#[\w\_]+', "HASHTAG", data["Sentence"][x])

        # Replace https by URL
        data["Sentence"][x] = re.sub('https[\w\./]*', "URL", data["Sentence"][x])

        # Replace all the special characters by ' '
        data["Sentence"][x] = re.sub(r'\W', ' ', data["Sentence"][x])

        # Substituting multiple spaces with single space
        data["Sentence"][x] = re.sub(r'\s+', ' ', data["Sentence"][x], flags=re.I)

        # Remove single space from the start
        data["Sentence"][x] = re.sub('^[\s]+', '', data["Sentence"][x])

        # Remove all single characters
        data["Sentence"][x] = re.sub(r'\s+[a-zA-Z]\s+', ' ', data["Sentence"][x])

        # Remove single characters from the start
        data["Sentence"][x] = re.sub(r'\^[a-zA-Z]\s+', ' ', data["Sentence"][x])

        # Converting to Lowercase
        data["Sentence"][x] =data["Sentence"][x].lower()


        if(data["Sentiment"][x] == "positive"):

            data["Sentiment"][x] = "1"

        elif(data["Sentiment"][x] == "negative"):

            data["Sentiment"][x] = "2"

        elif(data["Sentiment"][x]== "neutral"): 

            data["Sentiment"][x] = "0"

    return data


def get_tokenized_sentence_list(sentence_list):
    tokenized_sentence_list = []

    for sentence in sentence_list:
        tokens = word_tokenize(sentence)
        tokenized_sentence_list.append(tokens)

    return tokenized_sentence_list


def penn_to_wn(tag):
    """
    Convert between the PennTreebank tags to simple Wordnet tags
    """
    if tag.startswith('J'):
        return wn.ADJ
    elif tag.startswith('N'):
        return wn.NOUN
    elif tag.startswith('R'):
        return wn.ADV
    elif tag.startswith('V'):
        return wn.VERB
    return None


def get_sentiment(word, tag):
    """ returns list of pos neg and objective score. But returns empty list if not present in senti wordnet. """

    wn_tag = penn_to_wn(tag)
    if wn_tag not in (wn.NOUN, wn.ADJ, wn.ADV):
        return []

    lemmatizer = WordNetLemmatizer()

    lemma = lemmatizer.lemmatize(word, pos=wn_tag)
    if not lemma:
        return []

    synsets = wn.synsets(word, pos=wn_tag)
    if not synsets:
        return []

    # Take the first sense, the most common
    synset = synsets[0]
    swn_synset = swn.senti_synset(synset.name())

    return [swn_synset.pos_score(), swn_synset.neg_score(), swn_synset.obj_score()]


def calculate_sentival_sum(senti_vals):

    # append only non empty lists
    filtered_senti_vals = []
    for vals in senti_vals:
        if vals:
            filtered_senti_vals.append(vals)

    # sum all the list values
    if filtered_senti_vals:
        return [sum(x) for x in zip(*filtered_senti_vals)]

    else:
        return [0, 0, 0]


def normalize_values(value_list):
    sum_val = 0
    for value in value_list:
        sum_val += value

    if sum_val != 0:
      for i in range(0, len(value_list)):
          value_list[i] = value_list[i] / sum_val

    return value_list


def get_english_senti_scores(tokenized_sentences):
    ps = PorterStemmer()

    senti_scores = []
    for sentence_tokens in tokenized_sentences:
        sentence_tokens = [ps.stem(x) for x in sentence_tokens]

        pos_val = pos_tag(sentence_tokens)

        senti_vals = [get_sentiment(x, y) for (x, y) in pos_val]
        # print(sentence_tokens)
        # print(senti_vals)

        sum_sentivals = calculate_sentival_sum(senti_vals)
        # print(sum_sentivals)

        normalized_sum_sentivals = normalize_values(sum_sentivals)
      

        senti_scores.append(normalized_sum_sentivals)

    return senti_scores


def get_hindi_profanity_scores(sentence_list):
    hindi_score_data = pd.read_csv('/content/drive/My Drive/Colab Notebooks/Hinglish_Profanity_List.csv', encoding="latin1")

    profanity_scores = []
    for sentence in sentence_list:

        sum_scores = 0
        for hindi_word, score in zip(hindi_score_data['Hindi'], hindi_score_data['Profanity']):

            r = re.compile(r'\b%s\b' % hindi_word, re.I)
            if r.search(sentence.lower()) is not None:

                sum_scores += int(score)

        profanity_scores.append(sum_scores)

    return profanity_scores

data = pd.read_csv('/content/drive/My Drive/Colab Notebooks/training_data.csv',encoding="latin1")
data = preprocess_data(data)
print(data.head(10))

test_data = pd.read_csv('/content/drive/My Drive/Colab Notebooks/test_data.csv',encoding="latin1")
test_data = preprocess_data(test_data)
print(test_data.head(10))

sentences = data['Sentence'].values
sentiments = data['Sentiment'].values

train_sentences = sentences[:12000]
train_sentiments = sentiments[:12000]

#val_sentences = sentences[10000:12000]
#val_sentiments = sentiments[10000:12000]

test_sentences = sentences[12000:]
test_sentiments = sentiments[12000:]

tokenized_sentence_list = get_tokenized_sentence_list(sentences)

   senti_score_list = get_english_senti_scores(tokenized_sentence_list)

   hindi_profanity_score_list = get_hindi_profanity_scores(sentences)

   hindi_profanity_score_list = np.array(hindi_profanity_score_list)

   print(hindi_profanity_score_list)

positive_score = []
negative_score = []
objective_score = []

for x in senti_score_list:

  positive_score.append(x[0])
  negative_score.append(x[1])
  objective_score.append(x[2])

positive_score = np.array(positive_score)
negative_score = np.array(negative_score)
objective_score = np.array(objective_score)

english_positive_train_scores = positive_score[:12000]
#english_positive_validation_scores = positive_score[10000:12000]
english_positive_test_scores = positive_score[12000:]

english_negative_train_scores = negative_score[:12000]
#english_negative_validation_scores = negative_score[10000:12000]
english_negative_test_scores = negative_score[12000:]

english_objective_train_scores = objective_score[:12000]
#english_objective_validation_scores = objective_score[10000:12000]
english_objective_test_scores = objective_score[12000:]

hindi_profanity_train_score = hindi_profanity_score_list[:12000]
hindi_profanity_test_score = hindi_profanity_score_list[12000:]

train_input_fn = tf.estimator.inputs.numpy_input_fn(
    {'sentence': train_sentences,  'hin_prof_score': hindi_profanity_train_score}, train_sentiments, 
    batch_size=512, num_epochs=None, shuffle=True)

predict_train_input_fn = tf.estimator.inputs.numpy_input_fn(
    {'sentence': train_sentences,  'hin_prof_score': hindi_profanity_train_score}, train_sentiments, shuffle=False)

#predict_val_input_fn = tf.estimator.inputs.numpy_input_fn(
 #   {'sentence': val_sentences, 'eng_pos_score': english_positive_validation_scores, 'eng_neg_score': english_negative_validation_scores, 'eng_obj_score': english_objective_validation_scores}, val_sentiments, shuffle=False)

predict_test_input_fn = tf.estimator.inputs.numpy_input_fn(
    {'sentence': test_sentences,  'hin_prof_score': hindi_profanity_test_score}, test_sentiments, shuffle=False)

embedding_feature = hub.text_embedding_column(
    key='sentence', 
    module_spec="https://tfhub.dev/google/universal-sentence-encoder/2",
    trainable=False)


eng_pos_score = tf.feature_column.numeric_column(key='eng_pos_score')
eng_neg_score = tf.feature_column.numeric_column(key='eng_neg_score')
eng_obj_score = tf.feature_column.numeric_column(key='eng_obj_score')
hin_prof_score = tf.feature_column.numeric_column(key = 'hin_prof_score')

dnn = tf.estimator.DNNClassifier(
          hidden_units=[512, 128, 64, 32],
          feature_columns=[embedding_feature, hin_prof_score], 
          n_classes=3,
          label_vocabulary = ["0", "1", "2"],
          activation_fn=tf.nn.relu,
          dropout=0.1,
          optimizer=tf.train.AdagradOptimizer(learning_rate=0.05))

tf.logging.set_verbosity(tf.logging.ERROR)
import time

TOTAL_STEPS = 300
STEP_SIZE = 30
for step in range(0, TOTAL_STEPS+1, STEP_SIZE):
    print()
    print('-'*30)
    print('Training for step =', step)
    start_time = time.time()
    dnn.train(input_fn=train_input_fn, steps=STEP_SIZE)
    elapsed_time = time.time() - start_time
    print('Train Time (s):', elapsed_time)
    print('Eval Metrics (Train):', dnn.evaluate(input_fn=predict_train_input_fn))
    print('Eval Metrics (Test):', dnn.evaluate(input_fn=predict_test_input_fn))

dnn.evaluate(input_fn = predict_test_input_fn)