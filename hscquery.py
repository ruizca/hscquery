# -*- coding: utf-8 -*-
"""
Module for accesing the Hyper Suprime-Cam Subaru Strategic Program database.

Based on the python script developed by michitaro, NAOJ / HSC Collaboration.
Source: https://hsc-gitlab.mtk.nao.ac.jp/snippets/17
"""

import os
import json
import urllib2
import time
import sys
import csv
import getpass
import tempfile

from astropy import units as u
from astropy.table import Table


class QueryError(Exception):
    pass


class HSC(object):

    version = 20181012.1
    url = 'https://hsc-release.mtk.nao.ac.jp/datasearch/api/catalog_jobs/'


    def __init__(self, columns='object_id, ra, dec', survey='wide',
                 release_version='pdr1', user=None, password_env='HSCPASSW'):

        surveys = ['wide', 'deep', 'udeep']

        if not (survey in surveys):
            error_message = 'Unknown survey: {}'
            raise ValueError(error_message.format(survey))

        user, passw = self.login(user, password_env)
        self.credential = {'account_name': user, 'password': passw}
        self.columns = columns
        self.survey = survey
        self.release_version = release_version


    def login(self, user, password_env):
        
        if user is None:
            user = raw_input("HSC-SSP user: ")

        password_from_envvar = os.environ.get(password_env, '')
        if password_from_envvar != '':
            passw = password_from_envvar

        else:
            passw = getpass.getpass('password: ')

        return user, passw


    def query_region(self, coords, radius, catalog='forced'):
        """
        Returns an astropy Table object with all sources of 
        catalog within radius around coords.

        coords: search around this position (SkyCoord object)
        radius: search radius (Quantity object, in angular units)
        catalog: 'forced', 'meas', 'specz', 'random'
                 (see https://hsc-release.mtk.nao.ac.jp/schema/)
        """

        catalogs = ['forced', 'meas', 'specz', 'random']

        if not (catalog in catalogs):
            error_message = 'Unknown survey: {}'
            raise ValueError(error_message.format(catalog))

        table = '{}_{}.{}'.format(self.release_version, self.survey, catalog)
        
        query = 'SELECT {} FROM {} WHERE coneSearch(coord, {}, {}, {})'
        query = query.format(self.columns, table, 
                             coords.ra.deg, coords.dec.deg, 
                             radius.to(u.arcsec).value)

        with tempfile.NamedTemporaryFile() as temp:
            self.send_query(query, out_format='fits', output_file=temp.name)

            temp.seek(0)
            data_raw = Table.read(temp.name, format='fits')

        # Remove isnull columns
        columns = [col for col in data_raw.colnames 
                   if not col.endswith('_isnull')]

        return data_raw[columns]


    def send_query(self, sql, out_format='csv', 
                   delete_job=True, output_file=None):

        formats = ['csv', 'csv.gz', 'sqlite3', 'fits']

        try:
            if output_file is None:
                self.__preview(self.credential, sql, sys.stdout)

            else:
                if not (out_format in formats):
                    error_message = 'Unknown output format: {}'
                    raise ValueError(error_message.format(out_format))

                job = self.__submitJob(self.credential, sql, out_format)
                self.__blockUntilJobFinishes(self.credential, job['id'])

                with open(output_file, 'w') as output:
                    self.__download(self.credential, job['id'], output)

                if delete_job:
                    self.__deleteJob(self.credential, job['id'])

        except urllib2.HTTPError, e:
            if e.code == 401:
                print >> sys.stderr, 'invalid id or password.'

            if e.code == 406:
                print >> sys.stderr, e.read()

            else:
                print >> sys.stderr, e

        except QueryError, e:
            print >> sys.stderr, e

        except KeyboardInterrupt:
            if job is not None:
                self.__jobCancel(self.credential, job['id'])

            raise

    
    def __httpJsonPost(self, url, data):

        data['clientVersion'] = self.version
        postData = json.dumps(data)
        headers = {'Content-type': 'application/json'}

        return self.__httpPost(url, postData, headers)
    
    
    def __httpPost(self, url, postData, headers):

        req = urllib2.Request(url, postData, headers)
        res = urllib2.urlopen(req)

        return res
    
    
    def __submitJob(self, credential, sql, out_format, 
                    nomail=True, skip_syntax_check=True):

        url = self.url + 'submit'
        catalog_job = {
            'sql'                     : sql,
            'out_format'              : out_format,
            'include_metainfo_to_body': True,
            'release_version'         : self.release_version,
        }

        postData = {'credential': credential, 'catalog_job': catalog_job, 
                    'nomail': nomail, 'skip_syntax_check': skip_syntax_check}

        res = self.__httpJsonPost(url, postData)
        job = json.load(res)

        return job
    
    
    def __jobStatus(self, credential, job_id):

        url = self.url + 'status'
        postData = {'credential': credential, 'id': job_id}

        res = self.__httpJsonPost(url, postData)
        job = json.load(res)

        return job
    
    
    def __jobCancel(self, credential, job_id):

        url = self.url + 'cancel'
        postData = {'credential': credential, 'id': job_id}

        self.__httpJsonPost(url, postData)
    
    
    def __preview(self, credential, sql, out):

        url = self.url + 'preview'
        catalog_job = {
            'sql'             : sql,
            'release_version' : self.release_version,
        }
        postData = {'credential': credential, 'catalog_job': catalog_job}
        res = self.__httpJsonPost(url, postData)
        result = json.load(res)
    
        writer = csv.writer(out)
        for row in result['result']['rows']:
            writer.writerow(row)
    
        result_nrows = len(result['result']['rows'])
        if result['result']['count'] > result_nrows:
            error_message = 'only top {:d} records are displayed !'
            raise QueryError,  error_message.format(result_nrows)
    
    
    def __blockUntilJobFinishes(self, credential, job_id):

        max_interval = 5 * 60 # sec.
        interval = 1

        while True:
            time.sleep(interval)
            job = self.__jobStatus(credential, job_id)

            if job['status'] == 'error':
                raise QueryError, 'query error: {}'.format(job['error'])

            if job['status'] == 'done':
                break

            interval *= 2
            if interval > max_interval:
                interval = max_interval


    def __download(self, credential, job_id, out):

        url = self.url + 'download'
        postData = {'credential': credential, 'id': job_id}

        res = self.__httpJsonPost(url, postData)
        bufSize = 64 * 1<<10 # 64k

        while True:
            buf = res.read(bufSize)
            out.write(buf)
            if len(buf) < bufSize:
                break


    def __deleteJob(self, credential, job_id):
        url = self.url + 'delete'
        postData = {'credential': credential, 'id': job_id}

        self.__httpJsonPost(url, postData)
            

