# -*- coding: utf-8 -*-

'''
Copyright (c) 2012-2021 Roel Derickx, Paul Norman <penorman@mac.com>,
Sebastiaan Couwenberg <sebastic@xs4all.nl>, The University of Vermont
<andrew.guertin@uvm.edu>, github contributors

Released under the MIT license, as given in the file LICENSE, which must
accompany any distribution of this code.
'''

import logging
from lxml import etree

class OsmId:
    element_id_counter = 0
    element_id_counter_incr = -1

    @staticmethod
    def set_id(start_id, is_positive = False):
        OsmId.element_id_counter = start_id
        if is_positive:
            OsmId.element_id_counter_incr = 1


    @staticmethod
    def load_id(filename):
        with open(filename, 'r') as ff:
            OsmId.element_id_counter = int(ff.readline(20))
        logging.info("Starting counter value '%d' read from file '%s'.", \
                     OsmId.element_id_counter, filename)


    @staticmethod
    def save_id(filename):
        with open(filename, 'w') as ff:
            ff.write(str(OsmId.element_id_counter))
        logging.info("Wrote elementIdCounter '%d' to file '%s'", \
                     OsmId.element_id_counter, filename)



class OsmBoundary:
    def __init__(self):
        self.is_valid = False
        self.minlon = 0.0
        self.maxlon = 0.0
        self.minlat = 0.0
        self.maxlat = 0.0


    def add_envelope(self, minx, maxx, miny, maxy):
        if self.is_valid:
            self.minlon = min(self.minlon, minx)
            self.maxlon = max(self.maxlon, maxx)
            self.minlat = min(self.minlat, miny)
            self.maxlat = max(self.maxlat, maxy)
        else:
            self.is_valid = True
            self.minlon = minx
            self.maxlon = maxx
            self.minlat = miny
            self.maxlat = maxy


    def to_xml(self, significant_digits):
        xmlattrs = { 'minlon':(('%%.%df' % significant_digits) % self.minlon).strip('0'), \
                     'minlat':(('%%.%df' % significant_digits) % self.minlat).strip('0'), \
                     'maxlon':(('%%.%df' % significant_digits) % self.maxlon).strip('0'), \
                     'maxlat':(('%%.%df' % significant_digits) % self.maxlat).strip('0') }
        xmlobject = etree.Element('bounds', xmlattrs)

        return etree.tostring(xmlobject, encoding='unicode')



class OsmGeometry:
    def __init__(self):
        self.id = self.__get_new_id()
        self.tags = {}
        self.__parents = set()


    def __get_new_id(self):
        OsmId.element_id_counter += OsmId.element_id_counter_incr
        return OsmId.element_id_counter


    def _append_non_empty_tags(self, tags):
        for (key, value) in tags.items():
            if value:
                self.tags.update({ key: [ value ] })


    def addparent(self, parent):
        self.__parents.add(parent)


    def removeparent(self, parent):
        self.__parents.discard(parent)


    def get_parents(self):
        return self.__parents


    def to_xml(self, attributes, significant_digits):
        pass



class OsmNode(OsmGeometry):
    def __init__(self, x, y, tags):
        super().__init__()
        self.x = x
        self.y = y
        self._append_non_empty_tags(tags)


    def to_xml(self, attributes, significant_digits):
        xmlattrs = { 'visible':'true', \
                     'id':('%d' % self.id), \
                     'lat':(('%%.%df' % significant_digits) % self.y).strip('0'), \
                     'lon':(('%%.%df' % significant_digits) % self.x).strip('0') }
        xmlattrs.update(attributes)

        xmlobject = etree.Element('node', xmlattrs)

        for (key, value_list) in self.tags.items():
            tag = etree.Element('tag', { 'k':key, 'v':','.join(value_list) })
            xmlobject.append(tag)

        return etree.tostring(xmlobject, encoding='unicode')



class OsmWay(OsmGeometry):
    def __init__(self, tags):
        super().__init__()
        self.nodes = []
        self._append_non_empty_tags(tags)


    def to_xml(self, attributes, significant_digits):
        xmlattrs = { 'visible':'true', 'id':('%d' % self.id) }
        xmlattrs.update(attributes)

        xmlobject = etree.Element('way', xmlattrs)

        for node in self.nodes:
            nd = etree.Element('nd', { 'ref':('%d' % node.id) })
            xmlobject.append(nd)
        for (key, value_list) in self.tags.items():
            tag = etree.Element('tag', { 'k':key, 'v':','.join(value_list) })
            xmlobject.append(tag)

        return etree.tostring(xmlobject, encoding='unicode')



class OsmRelation(OsmGeometry):
    def __init__(self, tags):
        super().__init__()
        self.members = []
        self._append_non_empty_tags(tags)


    def get_member_role(self, member):
        member_roles = [ m[1] for m in self.members if m[0] == member ]
        member_role = member_roles[0] if any(member_roles) else ""
        return member_role


    def to_xml(self, attributes, significant_digits):
        xmlattrs = { 'visible':'true', 'id':('%d' % self.id) }
        xmlattrs.update(attributes)

        xmlobject = etree.Element('relation', xmlattrs)

        for (member, role) in self.members:
            member_type = None
            if type(member) == OsmNode:
                member_type = 'node'
            elif type(member) == OsmWay:
                member_type = 'way'
            elif type(member) == OsmRelation:
                member_type = 'relation'
            xmlmember = etree.Element('member', { 'type':member_type, \
                                                  'ref':('%d' % member.id), 'role':role })
            xmlobject.append(xmlmember)

        tag = etree.Element('tag', { 'k':'type', 'v':'multipolygon' })
        xmlobject.append(tag)
        for (key, value_list) in self.tags.items():
            tag = etree.Element('tag', { 'k':key, 'v':','.join(value_list) })
            xmlobject.append(tag)

        return etree.tostring(xmlobject, encoding='unicode')
