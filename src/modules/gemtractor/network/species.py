# This file is part of the GEMtractor
# Copyright (C) 2019 Martin Scharm <https://binfalse.de>
# 
# The GEMtractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# The GEMtractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging


class Species:
  """
  a species in a metabolite-reaction network
  """
  
  def __init__ (self, identifier, name):
    """
    :param identifier: the species' id
    :param name: the species' name
    """
    self.__logger = logging.getLogger(__name__)
    self.name = name
    self.identifier = identifier
    self._consumption = {"g":set (), "gc":set(), "r":set()}
    self._production = {"g":set (), "gc":set(), "r":set()}
    self.occurence = []
    
  def serialize (self):
    """
    serialize to a JSON-dumpable object
    """
    return {
      "id" : self.identifier,
      "name" : self.name,
      "occ" : self.occurence
      }
