#!/usr/bin/env python
# coding: utf-8

import os
from sqlalchemy import create_engine
import pymysql
import pymysql.cursors
import configparser
import pandas as pd
import logging
from graphdatascience import GraphDataScience
from neo4j import GraphDatabase
from pymongo import MongoClient, UpdateOne
from bson import ObjectId
from pymongo.server_api import ServerApi
from common.utils import get_config_dir
CONFIG_PATH = get_config_dir()


class mysqlDB(object):
    _defaults = {
    }
    @classmethod
    def get_defaults(cls, n):
        if n in cls._defaults:
            return cls._defaults[n]
        else:
            return "Unrecognized attribute name '" + n + "'"
    def __init__(self, **kwargs):
        self.__dict__.update(self._defaults)
        self.__dict__.update(kwargs)
        self._get_db_config()
        self._connect()

    def _get_db_config(self):
        self.db_info = {}
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        config_name = 'db_tpe'
        self.db_info['DESC'] = config.get(config_name, 'desc')
        self.db_info['DB_IP'] = config.get(config_name, 'db_ip')
        self.db_info['DB_PORT'] = config.get(config_name, 'db_port')
        self.db_info['DB_USERNAME'] = config.get(config_name, 'db_username')
        self.db_info['DB_PASSWORD'] = config.get(config_name, 'db_password')
        self.db_info['DB_NAME'] = config.get(config_name, 'db_name')
        logging.info(f'{config_name}: {self.db_info}')
        
    def _connect(self):
        self.engine = create_engine(f"mysql+pymysql://{self.db_info['DB_USERNAME']}:{self.db_info['DB_PASSWORD']}@{self.db_info['DB_IP']}:{self.db_info['DB_PORT']}/{self.db_info['DB_NAME']}?charset=utf8")        
        self.connection = pymysql.connect(host=self.db_info['DB_IP'], user=self.db_info['DB_USERNAME'], passwd=self.db_info['DB_PASSWORD'], db=self.db_info['DB_NAME'])
        
        
    def read_sql(self, sql_read):
        data = pd.read_sql(sql_read, self.engine)
        return data
    
    def to_sql(self, table, data, if_exists='append'):
        engine = self.engine
        if 'Error Log' in data.columns:
            data['Error Log'] = data['Error Log'].map(lambda x: x[:8000] if len(x) > 8000 else x)        
        data.to_sql(name=table, con=engine, if_exists=if_exists, index=False)
        
    def execute_sql(self, sql):
        self.engine.execute(sql)

    def execute_sql2(self, sql, values):
        self.connection.cursor().execute(sql, values) 
        self.connection.commit()
        #self.connection.close   

    def executemany_sql(self, sql, values):
        self.connection.cursor().executemany(sql, values)
        self.connection.commit()


class Neo4jDB(object):
    _defaults = {
        'config_name':'',
        'database':'calllog'
        }
    
    @classmethod
    def get_defaults(cls, n):
        if n in cls._defaults:
            return cls._defaults[n]
        else:
            return "Unrecognized attribute name '" + n + "'"        

    def __init__(self, **kwargs):
        self.__dict__.update(self._defaults)
        self.__dict__.update(kwargs)
        self._get_db_config()
        self.gds, self.driver = self._connect()
        
    def _get_db_config(self):
        self.db_info = {}
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        logging.info(self.config_name)
        self.db_info['URI'] = config.get(self.config_name, 'uri')
        self.db_info['USER'] = config.get(self.config_name, 'user')
        self.db_info['PASSWORD'] = config.get(self.config_name, 'password')
        logging.info(f'{self.config_name}: {self.db_info}')
        
    def _connect(self):
        url = self.db_info['URI']
        auth = (self.db_info['USER'], self.db_info['PASSWORD'])
        gds = GraphDataScience(url, auth=auth, database=self.database)
        #driver = GraphDatabase.driver(self.db_info['URI'], auth=(self.db_info['USER'], self.db_info['PASSWORD']))
        return gds, None
        
    def run_cypher(self, cypher):
        ret = self.gds.run_cypher(cypher)
        return ret
        
    def clear_Graph(self):
        cypher = '''MATCH (i)
        DETACH DELETE i
        '''
        self.run_cypher(cypher)
        
    def delete_relation(self, label1, prop1, val1, rel):
        cypher = f'''MATCH (n1:{label1} {{{prop1}: "{val1}"}})-[r:{rel}]->() DELETE r'''
        self.run_cypher(cypher)

    def get_node_qty(self):
        cypher = 'CALL apoc.meta.stats() YIELD labels RETURN labels'
        ret= self.run_cypher(cypher)
        return ret['labels'].iloc[0]


class MongoDB(object):
    _defaults = {
        'config_name':''
    }
    @classmethod
    def get_defaults(cls, n):
        if n in cls._defaults:
            return cls._defaults[n]
        else:
            return "Unrecognized attribute name '" + n + "'"

    _instance = None 
    def __new__(cls, *args, **kwargs): 
        if cls._instance is None: 
            cls._instance = super().__new__(cls) 
        return cls._instance    
        
    def __init__(self, **kwargs):
        self.__dict__.update(self._defaults)
        self.__dict__.update(kwargs)
        self._get_db_config()
        self._connect()

    def _get_db_config(self):
        self.db_info = {}
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        logging.info(self.config_name)
        
        if config.has_option(self.config_name, 'uri'):
            self.db_info['DESC'] = config.get(self.config_name, 'desc')
            self.db_info['URI'] = config.get(self.config_name, 'uri')
            self.db_info['DB_NAME'] = config.get(self.config_name, 'db_name')
        else:        
            self.db_info['DESC'] = config.get(self.config_name, 'desc')
            self.db_info['DB_IP'] = config.get(self.config_name, 'db_ip')
            self.db_info['DB_PORT'] = config.get(self.config_name, 'db_port')
            self.db_info['DB_USERNAME'] = config.get(self.config_name, 'db_username')
            self.db_info['DB_PASSWORD'] = config.get(self.config_name, 'db_password')
            self.db_info['DB_NAME'] = config.get(self.config_name, 'db_name')
        logging.info(f'{self.db_info}')
        
    def _connect(self):
        if 'URI' in self.db_info:
            self.client = MongoClient(self.db_info['URI'], server_api=ServerApi('1'))
        else:
            self.client = MongoClient(f"mongodb://{self.db_info['DB_USERNAME']}:{self.db_info['DB_PASSWORD']}@{self.db_info['DB_IP']}:{self.db_info['DB_PORT']}")
        self.db = self.client[self.db_info['DB_NAME']]

    def find(self, collection_name, query={}, fields={}, limit=0):
        collection = self.db[collection_name]
        if len(fields)==0:
            data = collection.find(query, limit=limit)
        else:
            data = collection.find(query, fields, limit=limit)
        return data
    
    def find_one(self, collection_name, query):
        collection = self.db[collection_name]
        data = collection.find_one(query)
        return data

    def insert_many(self, collection_name, documents):
        collection = self.db[collection_name]
        collection.insert_many(documents, ordered=False)
        
    def update_one(self, collection_name, query, update, upsert=False):
        collection = self.db[collection_name]
        collection.update_one(query, update, upsert=upsert)
        
    def update_many(self, collection_name, query, update):
        collection = self.db[collection_name]
        collection.update_many(query, update)
    
    def bulk_write(self, collection_name, bulk_operations):
        collection = self.db[collection_name]
        collection.bulk_write(bulk_operations)
    
    def get_collection(self, collection_name):
        collection = self.db[collection_name]
        return collection
    
    def count_documents(self, collection_name, query):
        collection = self.db[collection_name]
        qty = collection.count_documents(query)
        return qty
    
    def drop_duplicated(self, collection_name, delete=True):
        collection = self.db[collection_name]
        group_keys = {"key1": "$Service Tag", "key2": "$DPS Num", "key3":"$Dispatch Date", "key4":"$hashcode"}
        
        pipeline = [
            {
                '$sort': {
                    'Dispatch Date': -1
                }
            },
            {
                '$group': {
                    '_id': group_keys, 
                    'latest_doc': {'$first': '$$ROOT'}  # Keep the first document in each group (latest due to sorting)
                }
            },
            {
                '$replaceRoot': {'newRoot': '$latest_doc'}  # Replace the root with the latest document in each group
            }
        ]
        result = list(collection.aggregate(pipeline))
        ids_to_keep = [doc['_id'] for doc in result]
        
        result = collection.find({}, {'_id': 1})
        id_all = [doc['_id'] for doc in result]
        ids_to_del = set(id_all) - set(ids_to_keep)
        ids_to_del = list(ids_to_del)
        del_qty = len(ids_to_del)
        logging.info(f'Delete qty:{del_qty}')
        if delete:
            collection.delete_many({'_id': {'$in': ids_to_del}})
        
    def drop_collection(self, collection_name):
        self.db[collection_name].drop()
        
    def create_index(self, collection_name):
        collection = self.db[collection_name]
        index_keys = [('Service Tag', 1), ('DPS Num', 1), ('Dispatch Date', 1), ('etl_neo4j_done', 1)] 
        index_name = collection.create_index(index_keys)

    
