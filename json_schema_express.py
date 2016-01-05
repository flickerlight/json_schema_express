#!/usr/bin/env python

import json
import sys
import os
import random
from generators.std import *
#from generators.usr import *


class DataProducer:
    def __init__(self,schema,plugin_config=None):
        self.schema=json.loads(schema)
        self.plugin_cache={}
        self.object_defines={}
        self.type_vs_plugin={
            "number":"std_number_generator.StdNumberRandom",
            "boolean":"std_boolean_generator.StdBooleanRandom",
            "integer":"std_integer_generator.StdIntegerRandom",
            "string":"std_string_generator.StdStringRandom"
        }
        if plugin_config:
            for key,value in plugin_config.items():
                self.type_vs_plugin[key]=value
        self._parse_schema()

    def _parse_schema(self):
        self.object_defines['root']=self.schema
        #save all definitions for future refererence
        if 'definitions' in self.schema:
            for key, value in self.schema['definitions'].items():
                self.object_defines[key]=value

    def produce(self):
        return self.build_object('root',self.object_defines['root'])

    def build_object(self,obj_key,obj_def):
        if obj_def['type'] == 'object':
            result_object={}
            for key, definition in obj_def['properties'].items():
                prop_key = obj_key+'.'+key
                result_object[key] = self.build_object(prop_key,definition)
            return result_object
        elif obj_def['type'] in ['string','integer','number','boolean']:
            return self.build_value(obj_key,obj_def)
        elif obj_def['type'] == 'array':
            return self.build_array(obj_key,obj_def)
        else:
            #type is null
            return None

    def build_value(self,obj_key,obj_def):
        if '__generator' not in obj_def.keys():
            generator = self.get_generator(obj_key,self.type_vs_plugin[obj_def['type']],obj_def)
        else:
            #print "customer defined generator"
            generator = self.get_generator(obj_key,obj_def['__generator'],obj_def)
        return generator.generate()

    def build_array(self,obj_key,obj_def):
        result_array = []
        if 'minItems' in obj_def:
            self.minLength = obj_def['minItems']
        else:
            self.minLength = 1
        if 'maxItems' in obj_def:
            self.maxLength = obj_def['maxItems']
        else:
            self.maxLength = 10
        if 'uniqueItems' in obj_def:
            self.uniqueItems = obj_def['uniqueItems']
        else:
            self.uniqueItems = False

        if isinstance(obj_def['items'],list):
            for i in range(0,len(obj_def['items'])):
                prop_key = obj_key+'.'+str(i)
                result_array.append(self.build_object(prop_key, obj_def['items'][i]))
        else:
            actual_number = random.randrange(self.minLength,self.maxLength+1)
            prop_key = obj_key+'.'+obj_def['items']['type']
            i =0 
            while i < actual_number:
                temp = self.build_object(prop_key,obj_def['items'])
                if self.uniqueItems:
                    if temp not in result_array:
                        result_array.append(temp)
                        i+=1
                    else:
                        continue
                else:
                    result_array.append(temp)
                    i+=1
        return result_array

    def get_generator(self,obj_key, plugin_name, obj_def):
        if obj_key not in self.plugin_cache:
            generator=eval(plugin_name)(obj_def)
            self.plugin_cache[obj_key]=generator
        return self.plugin_cache[obj_key]