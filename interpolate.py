################################################################################
#  Copyright Adam J. Jackson (2015)                                            #
#                                                                              #
#   This program is free software: you can redistribute it and/or modify       #
#   it under the terms of the GNU General Public License as published by       #
#   the Free Software Foundation, either version 3 of the License, or          #
#   (at your option) any later version.                                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#   GNU General Public License for more details.                               #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
################################################################################

import numpy as np
from scipy.interpolate import interp1d, interp2d
from scipy import constants
from numpy import genfromtxt
import re

eV2Jmol = constants.physical_constants['electron volt-joule relationship'][0] * constants.N_A
eV2kJmol = constants.physical_constants['electron volt-joule relationship'][0] * constants.N_A / 1000
kB2JKmol =  constants.physical_constants['Boltzmann constant'][0] * constants.N_A

def get_potential_aims(file,property):
    """Thermodynamic property interpolation function. Requires phonopy-FHI-aims output file.
    Reads data for S and Cv expressed in J/K/mol, F and U in kJ/mol.
    Outputs data for S and Cv in kB/cell, U, F and TS in eV/cell.
    """
    data = genfromtxt(file)
    T = data[:,0]
    if property in ('Cv','Cp','heat_capacity','C'):
        potential = data[:,3] / kB2JKmol
    elif property in ('U','internal_energy'):
        potential = data[:,4] / eV2kJmol
    elif property in ('F','A','Helmholtz','free_energy'):
        potential = data[:,1] / eV2kJmol
    elif property in ('S','Entropy','entropy'):
        potential = data[:,2] / kB2JKmol
    elif property in ('TS'):
        potential = T*data[:,2]
    else:
        raise RuntimeError('Property not found')        

    thefunction = interp1d(T,potential,kind='linear')

    return thefunction

def get_potential_nist_table(file, property):
    """Thermodynamic property interpolation function. Requires NIST-JANAF table. All properties in J, mol and K"""
    data = genfromtxt(file,skip_header=2)
    T = data[:,0]
    if property in ('Cp','C','heat_capacity'):
        potential = data[:,1]
    elif property in ('S','entropy'):
        potential = data[:,2]
    elif property in ('H','enthalpy'): 
        potential = (data[:,4] - data[0,4])*1E3
    elif property in ('U','internal_energy'):  
        # U = H - PV; for ideal gas molar PV = RT so U = H - RT
        from scipy.constants import R as R
        potential = (data[:,4] - data[0,4])*1E3 - R*data[:,0]
    elif property in ('DH','Delta_H','standard_enthalpy_change'):
        potential = data[:,4]*1E3
    else:
        raise RuntimeError('Property not found')        

    thefunction = interp1d(T,potential,kind='cubic')
    return thefunction

def get_potential_sulfur_table(filename):
    """
    Read thermodynamic property as function of T, P from datafile.

    Datafile should be generated by the code at http://github.com/WMD-bath/sulfur-model
    or follow the same format

    """
    # Import chemical potential in J mol-1 vs T, P from file
    data = genfromtxt(filename, comments='#',delimiter=',')
    T = data[:,0].flatten()
    with open(filename,'r') as f:
        header=f.readline()
    P = [float(p) for p in re.findall(r'\d+.\d+',header)]
    thefunction = interp2d(T,np.log(P),data[:,1:].transpose(), kind='cubic')

    def lin_P_function(T,P):
        return thefunction(T,np.log(P))
        
    return lin_P_function
