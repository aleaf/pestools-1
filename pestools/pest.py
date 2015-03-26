# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 13:35:24 2015

@author: egc
"""
import os
import numpy as np
import pandas as pd
from mat_handler import jco as Jco
from mat_handler import cov as Cov
from pst_handler import pst as Pst
from parsen import ParSen
from Cor import Cor


class Pest(object):
    """
    base class for PEST run
    contains run name, folder and some control data from PEST control file
    also has methods to read in parameter and observation data from PEST control file

    could also be a container for other global settings
    (a longer run name to use in plot titles, etc)

    basename : string
    pest basename or pest control file (includes path)
    """

    def __init__(self, basename, obs_info_file=None):

        self.basename = os.path.split(basename)[-1].split('.')[0]
        self.run_folder = os.path.split(basename)[0]
        if len(self.run_folder) == 0:
            self.run_folder = os.getcwd()

        self.pstfile = os.path.join(self.run_folder, self.basename + '.pst')
        
        # Thinking this will get pass along later to the Res class or similar
        self.obs_info_file = obs_info_file
    
    @property    
    def _jco(self):
        '''
        Matrix class of jco
        '''
        jco = Jco()
        jco.from_binary(os.path.splitext(self.pstfile)[0]+'.jco')
        return jco
    @property
    def jco_df(self):
        '''
        DataFrame of jco
        '''
        jco_df = self._jco.to_dataframe()
        return jco_df

    @property
    def pst(self):
        '''
        Pst Class
        '''
        pst = Pst(self.pstfile)
        return pst
        

    def parsen(self, **kwargs):
        '''
        ParSen class
        '''
        parsen = ParSen(basename=self.pstfile, jco_df = self.jco_df,
                        res_df = self.res_df, 
                        parameter_data = self.parameter_data, **kwargs)
        return parsen
        
    @property
    def res_df(self):
        '''
        Residual DataFrame
        '''
        res = self.pst.res
        return res

    @property
    def parameter_data(self):
        '''
        DataFrame of parameter data
        '''
        parameter_data = self.pst.parameter_data
        return parameter_data
        
    @property
    def observation_data(self):
        '''
        DataFrame of observation data
        '''
        observation_data = self.pst.observation_data
        return observation_data

    @property
    def obs_groups(self):
        '''
        List of observation groups
        '''
        obs_groups = self.pst.obs_groups
        return obs_groups
        
    @property
    def _cov(self):
        weights = self.res_df['weight'].values
        phi = self.pst.phi
        pars = self._jco.col_names
        
        # Calc Covariance Matrix
        # See eq. 2.17 in PEST Manual
        # Note: Number of observations are number of non-zero weighted observations
        q = np.diag(np.diag(np.tile(weights**2, (len(weights), 1))))
        cov = np.dot((phi/(np.count_nonzero(weights)-len(pars))),
                     (np.linalg.inv(np.dot(np.dot(self._jco.x.T, q),self._jco.x))))
        cov = Cov(x=cov, names = pars)
        return cov

    @property
    def cov_df(self):
        cov_df = self.cov.to_dataframe()
        return cov_df
        
    @property
    def cor(self):
        return Cor(self._cov)

    def _read_obs_info_file(self, obs_info_file, name_col='Name', x_col='X', y_col='Y', type_col='Type'):
        """Bring in ancillary observation information from csv file such as location and measurement type
        ATL: not sure if this is ultimately where this should go, but following the old structure for now
        """
        self.obsinfo = pd.read_csv(obs_info_file, index_col=name_col)
        self.obsinfo.index = [n.lower() for n in self.obsinfo.index]

        # remap observation info columns to default names
        self.obsinfo.rename(columns={x_col: 'X', y_col: 'Y', type_col: 'Type'}, inplace=True)

        # make a dataframe of observation type for each group
        if 'Type' in self.obsinfo.columns:
            self._read_obs_data()
            # join observation info to 'obsdata' so that the type and group for each observation are listed
            self.obsinfo = self.obsinfo.join(self.obsdata['OBGNME'], lsuffix='', rsuffix='1', how='inner')
            self.obsinfo.rename(columns={'OBGNME': 'Group'}, inplace=True)
            self.obstypes = self.obsinfo.drop_duplicates(subset='Group').ix[:, ['Group', 'Type']]
            self.obstypes.index = self.obstypes.Group
            self.obstypes = self.obstypes.drop('Group', axis=1)

          
if __name__ == '__main__':
    p = Pest(r'C:\Users\egc\Desktop\identpar_testing\ppestex\test')
#    jco2 = Matrix()
#    jco2.from_binary(r'C:\Users\egc\Desktop\identpar_testing\ppestex\test.jco')
#    jco3 = Jco()
#    jco3.from_binary(r'C:\Users\egc\Desktop\identpar_testing\ppestex\test.jco')
    parsen = Pest(r'C:\Users\egc\pest_tools-1\cc\columbia')