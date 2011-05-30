#!/usr/bin/env python

# Copyright (c) 2009 Mark Reid <mindmark@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import os
import re
import uuid

def stripComments(string):
    c = re.compile('^[/][/].*')
    comments = []
    for line in string.splitlines():
        comment = c.findall(line)
        if comment:
            comments.extend(comment)
    for item in comments:
        string = string.replace(item,'')
        
    return string


def isfloat(value):
    if value.count('.') == 1:
        if value.replace('.','').isdigit():
            return True
        else:
            return False
    else:
        return False


class Node(object):
    def __init__(self,nodeName=None, nodeType=None, parameters=[]):
        self.ui = {}
        self.nodeName = nodeName
        self.nodeType = nodeType
        self.parameters = parameters
        
        self.inputs = {}
        self.expressions = {}
    
    def getInputNodeNames(self):
        """returns lists of nodes conected"""
        return self.inputs.keys()
        
    def setInputConnection(self,nodeName,paramIndex):
        if self.inputs.has_key(nodeName):
            self.inputs[nodeName].append(paramIndex)
        else:
            self.inputs[nodeName] = [paramIndex]

        self.parameters[paramIndex] = nodeName
    def addExpressionConnection(self,nodeName,paramIndex):
        if self.expressions.has_key(nodeName):
            self.expressions[nodeName].append(paramIndex)
        else:
            self.expressions[nodeName] = [paramIndex]
            
    def getInputExpressionNodeNames(self):
        return self.expressions.keys()
            
    def dissconnectAll(self):
        inputlist = []
        for node,value in self.inputs.items():
            for index in value:
                self.setInputConnection('0',index)
                inputlist.append(index)
        self.inputs = {'0':inputlist}
    
    def renameConnection(self,oldName,newName):
        if self.inputs.has_key(oldName):
            value = self.inputs.pop(oldName)
            self.inputs[newName] = value
            for index in self.inputs[newName]:
                self.parameters[index] = newName
        if self.expressions.has_key(oldName):
            value = self.expressions.pop(oldName)
            #print value
            for index in value:
                #print self.parameters[index], '--->', oldName
                self.parameters[index] = self.parameters[index].replace(oldName,newName)
                #print self.parameters[index]
            self.expressions[newName] = value

    def listToString(self,x):
        cleanlist = []
        for item in x:
            cleanlist.append(str(item))
        
        return ', '.join(cleanlist)
        
    def getParamerIndex(self,value):
        return self.parameter.index(value)

    
    def dumpUi(self):
        ui = {}  
        for item,value in self.ui.items():
            ui['nodeView.%s.%s' % (self.nodeName,item)] = value
        return ui
    
    def dump(self):
        dump = "%s = %s(%s);" % (self.nodeName,self.nodeType, self.listToString(self.parameters))
        #return '\n'.join(textwrap.wrap(dump))
        return dump
class hiddenNode(Node):
    
    def dump(self):
        dump =  "%s(%s);" % (self.nodeType, ", ".join(self.parameters))
    
        return dump

class uiNode(dict):
    def __init__(self):
        super(uiNode,self).__init__()
        #self.nodeName =
    
    def listToString(self,x):
        cleanlist = []
        for item in x:
            cleanlist.append(str(item))
        
        return ', '.join(cleanlist)
    
    def dumpDict(self):
        return self.copy()
    def addDict(self,dictionary):
        for item,value in dictionary.items():
            self[item] = value
    
    def dump(self):
        itempairs = []
        sortedkeys = sorted(self.keys())
        
        for item in sortedkeys:
            itempairs.append(', '.join(['"%s"' % item, '"%s"' % self[item]]))
            
        dump = 'SetKey(\n    %s\n);' % ',\n    '.join( itempairs)
        return dump  
    
    
class groupNode(uiNode):
    def __init__(self,nodeName):
        super(groupNode,self).__init__()
        self.nodeName = nodeName
        self.nodeType = None
        #self.children = []
    
    def dumpDict(self):
        ui = {}
        for item,value in self.items():
            v = value
            if item == 'children':
                v = ','.join(value) + ','
            ui['nodeView.%s.%s' %(self.nodeName,item)] = v
        return ui
    
    def renameNode(self,oldName,newName):
        if self.has_key('children'):
            if oldName in self['children']:
                self['children'].remove(oldName)
                self['children'].append(newName)
    
    def dump(self):
        itempairs = []
        for item,value in self.items():
            v = value
            if item == 'children':
                v = self.listToString(value)#','.join(value) + ','
                
            itempairs.append(', '.join(['"nodeView.%s.%s"' % (self.nodeName,item), '"%s"' % v]))
        
        dump = 'SetKey(\n    %s\n);' % ',\n    '.join( itempairs)
        
class interfaceNode(uiNode):
    def __init__(self):
        super(interfaceNode,self).__init__()
        self.groups = {}
        
    def getNodeKeys(self,key):
        nodekeys = []
        
        for item in self:
            if item.count(key):
                nodekeys.append(item)
        
        return nodekeys
    def dumpDict(self):
        ui = uiNode()
        ui.addDict(self.copy())
        for group in self.groups:
            ui.addDict(self.groups[group].dumpDict())
        ui['nodeView.groups'] = ','.join(self.groups.keys()) + ','
        return ui

class globalNode(uiNode):
    
    def __init__(self):
        super(globalNode,self).__init__()
        self.proxyPaths = []
        self._quotes = ['TimeRange','UseProxy','TimecodeMode','ProxyFilter','Audio']
    
    def addDict(self,item):
        for key , value in  item.items():
            if key == 'DefineProxyPath':
                self.proxyPaths.append(value)
            else:
                if isinstance(value,list):
                    if len(value) == 1:
                        if key in self._quotes:
                            parameters = value[0].rstrip('"').lstrip('"')
                        else:
                            parameters = value[0]
                    else:
                        parameters = value
                self[key] = parameters
    
    def dump(self):
        dump = ''      
        for item,value in self.items():
            if isinstance(value,list):
                parameters = self.listToString(value)#','.join(value)
            else:
                if item in self._quotes:
                    parameters = '"%s"' % value
                else:
                    parameters = value
            nodeString = 'Set%s(%s);\n' % (item,parameters)
            dump += nodeString
        dump += '\n'
        for item in self.proxyPaths:
            dump += 'DefineProxyPath(%s);\n' % self.listToString(item)#', '.join(item)
        return dump
    
class nodeGraph(dict):
    def __init__(self):
        super(nodeGraph,self).__init__()
        self.ui =interfaceNode()
        self.globals = globalNode()
        self._graphConstructed = False
        
    def calculateConnections(self,nodeName):
                    
        for i, param in enumerate(self[nodeName].parameters):
            if param in self.keys():
                self[nodeName].setInputConnection(param,i)

            elif param.isdigit() == False and isfloat(param) == False:
                no_quotes = remove_quoted(param)
                if no_quotes:
                    for node in self.keys():
                        
                        if no_quotes.count(node):
                            #if node == 'Generic_Buddy_File_In':
                            #    print nodeName, param
                            self[nodeName].addExpressionConnection(node,i)

        
    def addNode(self,node):
        if self._graphConstructed:
            self[node.nodeName] = node
            self.calculateConnections(node.nodeName)
                                
        else:
            self[node.nodeName] = node

    def constructGraph(self):
        for key,item in self.items():
            nodeName = item.nodeName
            self.calculateConnections(nodeName)

        self._graphConstructed = True

    def getNodeInputs(self,nodeName):
        return self[nodeName].inputs
        
    def getNodeOutputs(self, nodeName):
        assert nodeName in self.keys()
        outputs = {}
        for node in self:
            if self[node].inputs.has_key(nodeName):
                outputs[node] = self[node].inputs[nodeName]
        return outputs
    
    def getNodeExpressionOutputs(self,nodeName):
        assert nodeName in self.keys()
        outputs = {}
        for node in self:
            if self[node].expressions.has_key(nodeName):
                #print nodeName, '****', node,self[node].expressions[nodeName]
                outputs[node] = self[node].expressions[nodeName]
                
        return outputs

    def renameNode(self,oldName,newName):
        if newName in self.keys():
            raise Exception()
        nodeOutputs = self.getNodeOutputs(oldName)
        expressionOutputs = self.getNodeExpressionOutputs(oldName)
        
        for outname,value in nodeOutputs.items():
            self[outname].renameConnection(oldName,newName)
                
        for outname,value in expressionOutputs.items():
            self[outname].renameConnection(oldName,newName)
        for group in self.ui.groups:    
            self.ui.groups[group].renameNode(oldName,newName)
        
        node = self.pop(oldName)
        node.nodeName = newName
        self[newName] = node
    
    def extractNode(self,nodeName):
        nodeOutputs = self.getNodeOutputs(nodeName)
        nodeInputs = self.getNodeInputs(nodeName)
        if nodeInputs:
            inputNodeNames = nodeInputs.keys()
        else:
            inputNodeNames = [0]
        
        
        self[nodeName].dissconnectAll()
        
        for output, value in nodeOutputs.items():
            for index in value:
                self[output].setInputConnection(inputNodeNames[0],index)
        
    def deleteNode(self,nodeName):
        assert nodeName in self.keys()
        nodeOutputs = self.getNodeOutputs(nodeName)
        for output, value in nodeOutputs.items():
            for index in value:
                self[output].setInputConnection('0',index)
  
        self.pop(nodeName)
   
    def topologicalSort(self):
        graph = {}
        def add_node(graph,node):
            if not graph.has_key(node):
                graph[node] = [0]
        def add_arc(graph,fromnode,tonode):
            graph[fromnode].append(tonode)
            graph[tonode][0] = graph[tonode][0] + 1
            
            
        def get_roots(graph):
            roots = []
            for node,nodeinfo in graph.items():
                if nodeinfo[0] == 0:
                    roots.append(node)
            return roots
            
        for node in self.keys():
            add_node(graph,node)
        
        for node in self:
            nodeOutputs = self.getNodeOutputs(node)
            for out in nodeOutputs:
                #print node,out
                #for connection in nodeOutputs[out]:
                add_arc(graph,node,out)
            nodeExpressionOutputs = self.getNodeExpressionOutputs(node)
            for out in nodeExpressionOutputs:
                #print out
                add_arc(graph,node,out)
                
                
        roots = get_roots(graph)
        
        sorted_graph = []
        layer = 0
        while len(roots) != 0:       
            root = roots.pop()
            sorted_graph.append(root)
            for child in graph[root][1:]:
                graph[child][0] = graph[child][0] -1
                if graph[child][0] == 0:
                    layer += 1
                    roots.append(child)
            del graph[root]
            
        if len(graph.items()) != 0:
            print'*****Graph Problem'
            print graph
            for item,value in graph.items():
                
                
                sorted_graph.append(item)
                
            #return None

        return sorted_graph
    
    def renameGroup(self,oldName,newName):
        if self.ui.groups.has_key(oldName):
            group = self.ui.groups.pop(oldName)
            group.nodeName = newName
            self.ui.groups[newName] = group
    
    def getTree(self,nodeName):
        pass
    
    def getRoot(self,nodeName):
        pass
    
    def getGuiNodeBbox(self):
        xlist = []
        ylist = []
        for nodeName, node in self.items():
            if node.ui.has_key('x'):
                xlist.append(float(node.ui['x']))
            if node.ui.has_key('y'):
                ylist.append(float(node.ui['y']))
        return (min(xlist),min(ylist),max(xlist),max(ylist))
    
    def addGraph(self,graph):
        
        def get_center(g):
            xmin,ymin,xmax,ymax = g.getGuiNodeBbox()
            xcenter = ((xmax - xmin) /2) + xmin
            ycenter = ((xmax - ymin) /2) + ymin
            
            xraduis = (xmax - xmin) /2
            yraduis = (ymax - ymin) /2
            radius = xraduis #max(xraduis,yraduis)
            
            return (radius,xcenter,ycenter)
        
        radius,xcenter,ycenter = get_center(self)
        radius2,xcenter2,ycenter2 = get_center(graph)
        
        offestx = (xcenter2 - xcenter) -  (radius + radius2)
        offesty = (ycenter2 - ycenter) #+ radius + radius2 #+ radius + radius2
        
        rename_nodes = []
        for nodeName,node in graph.items():
            if node.ui.has_key('x'):
                graph[nodeName].ui['x'] = float(node.ui['x']) - offestx
            if node.ui.has_key('y'):
                graph[nodeName].ui['y'] = float(node.ui['y']) - offesty
                
            if nodeName in self.keys():
                newName = nodeName + '_1'
                while True:
                    if newName in self.keys():
                        newName += '_1'
                    else:
                        break
                rename_nodes.append((nodeName,newName))
        for oldName, newName in rename_nodes:
            graph.renameNode(oldName,newName)
        grouprenames = []
        for group in graph.ui.groups:
            if group in self.ui.groups:
                newName = group + '_1'
                while True:
                    if newName in self.ui.groups:
                        newName += '_1'
                    else: break
                grouprenames.append((group,newName))
        
        for oldName,newName in grouprenames:
            graph.renameGroup(oldName,newName)
            
        for nodeName,node in graph.items():
            self[nodeName] = node
        for group in graph.ui.groups:
            if graph.ui.groups[group].has_key('x'):

                graph.ui.groups[group]['x'] = float(graph.ui.groups[group]['x']) - offestx
            if graph.ui.groups[group].has_key('y'):
                graph.ui.groups[group]['y'] = float(graph.ui.groups[group]['y']) - offesty
                
        
            self.ui.groups[group] = graph.ui.groups[group]
        
    #def get
            
    def dump(self,ui=True):
        ui = uiNode()     
        ui.addDict(self.ui.dumpDict())
        dump = ''
        dump += self.globals.dump()
        for item in self.topologicalSort():
            dump += self[item].dump() + '\n'
            ui.addDict(self[item].dumpUi())         
        dump += ui.dump()
        return dump
    
def remove_quoted(string):
    p = re.compile('["].*?["]')
   #p2 = re.compile("['].*?[']")
    cleanstring = string
    for item in p.findall(string):
        cleanstring = cleanstring.replace(item,'')
        
    #for item in p2.findall(cleanstring):
        
        
        
    return cleanstring



def Parse(string):
    
    graph = nodeGraph()
    start = 0
    ignore = 0	
    quoted = False

    string = stripComments(string)
    
    for i,item in enumerate(string):
        if item in ['(','{']:
            ignore += 1
        elif item in [')','}']:
            ignore -= 1
        elif item in ['"']:
            if quoted:
                if string[i-1] != '\\':
                    quoted = False
            else:
                quoted = True			
        elif quoted == False and ignore == 0 and item in [';']:
            nodeString = string[start:i].replace('\n','')
            node = nodeParser(nodeString)
            if isinstance(node, interfaceNode):
                graph.ui = node
            elif isinstance(node, dict):
                #print node
                graph.globals.addDict(node)
                
            else:
                graph.addNode(node)
            start = i + 1
            
    for node in graph:
        uikey = 'nodeView.%s.' % node
        nodekeys = graph.ui.getNodeKeys(uikey)
        for key in nodekeys:
            cleankey = key.replace(uikey, '')
            graph[node].ui[cleankey] = graph.ui[key]
            del graph.ui[key]
    
    graph.constructGraph()
    return graph

def nodeParser(string):
    p = re.compile('[(].*[)]',re.DOTALL)
    parameterString = p.findall(string)
    parameters =[]
    if parameterString:
        parameterString = parameterString[0]
        string = string.replace(parameterString,'')
        parameters = parameterParser(parameterString[1:-1])
        
    name =  string.replace(' ','').split('=')
    nodeType = name[-1]
    nodeName = None
    
    if len(name) == 2:
        nodeName = name[0]
        return Node(nodeName,nodeType,parameters)
    elif nodeType == 'SetKey':
        return interfaceParser(parameters)
    
    elif nodeType.count('Set'):
        return {nodeType.replace('Set',''):parameters}
    elif nodeType.count('DefineProxyPath'):
        return {nodeType:parameters}
    else:
        num = uuid.uuid1()
        name = '_hidden_%s_%s' % (nodeType, str(num))
        return hiddenNode(name,nodeType,parameters)

def parameterParser(string):    
    parameterValues = []
    start = 0
    ignore = 0	
    quoted = False
    
    for i,item in enumerate(string):
        if item in ['(','{','[']:
            ignore += 1
        elif item in [')','}',']']:
            ignore -= 1
        elif item in ['"']:
            if quoted:
                if string[i-1] != '\\':
                    quoted = False
            else:
                quoted = True

        elif quoted == False and ignore == 0 and item in [',']:
            value = string[start:i]
            parameterValues.append(value.lstrip().rstrip())            
            start = i+1

    parameterValues.append(string[start:].lstrip().rstrip())
    return parameterValues

def interfaceParser(parameters):
    interfacekeys = interfaceNode()
    def strip_quotes(string):
        return string.rstrip('"').lstrip('"')
    
    for i,item in enumerate(parameters[::2]):
        key = strip_quotes(item)
        value = strip_quotes(parameters[i*2+1])
        if key == 'nodeView.groups':
            for item in value.rstrip(',').split(','):
                interfacekeys.groups[item] = groupNode(item)           
        else:
            interfacekeys[key] = value
            
    for item in interfacekeys.groups:
        groupkey = 'nodeView.%s.' % item
        uikeys = interfacekeys.getNodeKeys(groupkey)
        for key in uikeys:
            cleankey = key.replace(groupkey,'')
            if cleankey == 'children':
                interfacekeys.groups[item][cleankey] = interfacekeys[key].rstrip(',').split(',')
            else:
                interfacekeys.groups[item][cleankey] = interfacekeys[key]
            del interfacekeys[key]
    
    return interfacekeys



