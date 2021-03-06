import numpy as np
import re

from sentiment_analysis import load_sentiment_model, load_tagging_model, sentiment_analysis
from mem_absa.load_data import init_word_embeddings
from mem_absa.load_data import read_sample
from mem_absa.mapping import mapping_sentiments

import configuration as configuration

import mysql.connector

import spacy
from pyfasttext import FastText

fr_nlp=spacy.load("fr")

wiki_model=FastText()
wiki_model.load_model(configuration.pathFasttext)

# connection à la BD
conn=mysql.connector.connect(host="localhost", user="root", password="root", database="resolution")


def generate_review_data():
    cursor=conn.cursor()
    cursor.execute("select distinct code_etab from resolution.contributions_etab_nihel where code_an8=54053000 limit 300")
    etabs=cursor.fetchall()
    data=[]
    # with open(file, "w") as f:

    for etab in etabs:
        etab_vect=[]
        cursor.execute("SELECT id_contrib,comment,note_globale FROM resolution.contributions_etab_nihel "
                       "where code_an8=54053000 and code_etab='" + str(etab[0]) + "' limit 3")
        etab_reviews=cursor.fetchall()

        for i in range(min(len(etab_reviews), 3)):
            # print(etab[0],etab_reviews[i][0],etab_reviews[i][1],etab_reviews[i][2])
            etab_vect.append([etab[0], etab_reviews[i][0], etab_reviews[i][1], etab_reviews[i][2]])
        # f.write(etab_reviews[i][1] + "\n")
        if len(etab_reviews) < 3:
            for j in range(3 - len(etab_reviews)):
                # print(etab[0],"-","-","-")
                etab_vect.append([etab[0], "-", "-", "-"])
                #                f.write("\n")
        data.append(etab_vect)
    return data


def main():
    # sequence tagging
    model_tag=load_tagging_model()
    model_sa, FLAGS, source_count, source_word2idx=load_sentiment_model(fr_nlp, wiki_model)

    profs=generate_review_data()

    # with open(configuration.filename_reviews, "r") as f:
    #    reviews=[]
    #    for line in f:
    #        reviews.append(line)

    # with open(configuration.filename_aspects, 'rb') as fp:
    #    aspects=pickle.load(fp)
    csv_file=open(configuration.filename_csv, 'w')
    csv_file.write("code_etab;id_contrib;comment_1;note_globale_1;"
                   "sentiment_SERVICE_1;target_SERVICE_1;sample_SERVICE_1;"
                   "sentiment_AMBIANCE_1;target_AMBIANCE_1;sample_AMBIANCE_1;"
                   "sentiment_QUALITY_1;target_QUALITY_1;sample_QUALITY_1;"
                   "sentiment_PRICE_1;target_PRICE_1;sample_PRICE_1;"
                   "sentiment_GENERAL_1;target_GENERAL_1;sample_GENERAL_1;"
                   "sentiment_LOCATION_1;target_LOCATION_1;sample_LOCATION_1;comment_2;note_globale_2;"
                   "sentiment_SERVICE_2;target_SERVICE_2;sample_SERVICE_2;"
                   "sentiment_AMBIANCE_2;target_AMBIANCE_2;sample_AMBIANCE_2;"
                   "sentiment_QUALITY_2;target_QUALITY_2;sample_QUALITY_2;"
                   "sentiment_PRICE_2;target_PRICE_2;sample_PRICE_2;"
                   "sentiment_GENERAL_2;target_GENERAL_2;sample_GENERAL_2;"
                   "sentiment_LOCATION_2;target_LOCATION_2;sample_LOCATION_2;comment_3;note_globale_3;"
                   "sentiment_SERVICE_3;target_SERVICE_3;sample_SERVICE_3;"
                   "sentiment_AMBIANCE_3;target_AMBIANCE_3;sample_AMBIANCE_3;"
                   "sentiment_QUALITY_3;target_QUALITY_3;sample_QUALITY_3;"
                   "sentiment_PRICE_3;target_PRICE_3;sample_PRICE_3;"
                   "sentiment_GENERAL_3;target_GENERAL_3;sample_GENERAL_3;"
                   "sentiment_LOCATION_3;target_LOCATION_3;sample_LOCATION_3;"
                   "summary_SERVICE;summary_AMBIANCE;"
                   "summary_QUALITY;summary_PRICE;"
                   "summary_GENERAL;summary_LOCATION\n")

    # k=0
    for prof in profs:
        csv_file.write(str(prof[0][0]) + ";" + str(prof[0][1]))
        tab_sent=[0, 0, 0, 0, 0, 0]
        tab_sum=[0, 0, 0, 0, 0, 0]

        for i in range(len(prof)):
            all_aspect_words, all_aspect_categories, all_predictions=[], [], []
            samples={}
            # for review, aspects_,rev in zip(reviews, aspects,data):
            csv_file.write(";\"" + str(re.sub('\"', '&quot', prof[i][2]) + "\"" + ";" + str(prof[0][3])))
            review=prof[i][2]
            review=review.strip()
            sentences=re.split('\.+|\!|\?', review)

            for sentence in sentences:
                sentence_nlp=fr_nlp(sentence)
                words_raw=[]
                words_raw.extend([sp.text for sp in sentence_nlp])
                # print(words_raw)
                _, aspects=model_tag.predict(words_raw)
                # print(res)
                if len(aspects) > 0:
                    aspect_words=np.array(aspects)[:, 0]
                    all_aspect_words.extend(aspect_words)

                    aspect_categories=np.array(aspects)[:, 1]
                    all_aspect_categories.extend(aspect_categories)

                    aspect_idx=np.array(aspects)[:, 2]

                    test_data=read_sample(fr_nlp, review, aspect_words, aspect_idx, source_count, source_word2idx)
                    FLAGS.pre_trained_context_wt=init_word_embeddings(wiki_model, source_word2idx, FLAGS.nbwords)
                    FLAGS.pre_trained_context_wt[FLAGS.pad_idx, :]=0

                    predictions=model_sa.predict(test_data, source_word2idx)
                    for asp, cat, pred in zip(aspect_words, aspect_categories, predictions):
                        all_predictions.append(pred)
                        # print(asp, " : ", str(cat), " =>", mapping_sentiments(pred), end=" ; ")
                        sample=[s.strip() for s in re.split('[\.\?!,;:]', review) if
                                re.sub(' ', '', asp.lower()) in re.sub(' ', '', s.lower())][0]
                        # print(sample)
                        samples[str(cat) + '_' + str(pred)]=sample

            # summary review
            # print("\n------SUMMARY REVIEW-------")
            if len(all_aspect_words) > 0:
                categories=['SERVICE', 'AMBIANCE', 'QUALITE', 'PRIX', 'GENERAL', 'LOCALISATION']
                j=0
                for categ in categories:
                    asp_cat=""
                    exists=False
                    total=0
                    val=0
                    for asp, cat, pred in zip(all_aspect_words, all_aspect_categories, all_predictions):
                        if str(cat) == categ:
                            exists=True
                            total+=1
                            val+=pred
                            asp_cat+=asp + ", "
                    if exists:
                        tab_sent[j]+=round(val / total)
                        tab_sum[j]+=1
                        csv_file.write(
                            ";\"" + mapping_sentiments(round(val / total)) + "\";\"" + asp_cat[0:-2] + "\";\"")
                        # print(categ, " ", mapping_sentiments(round(val / total)), "exemple : ")
                        try:
                            csv_file.write(samples[categ + '_' + str(int(round(val / total)))] + "\"")
                        # print(samples[categ + '_' + str(int(round(val / total)))])
                        except:
                            csv_file.write("\"conflict\"")
                            print("conflict")
                    else:
                        csv_file.write(";\"-\";\"-\";\"-\"")
                    j+=1
            else:
                csv_file.write(";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-"
                               "\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\";\"-\"")
                #   print("PAS D'ASPECTS !")
                # k+=1
        for l in range(len(tab_sent)):
            if tab_sum[l] == 0:
                csv_file.write(";\"-\"")
            else:
                csv_file.write(";\"" + mapping_sentiments(round(tab_sent[l] / tab_sum[l])) + "\"")
        csv_file.write("\n")


if __name__ == "__main__":
    main()
