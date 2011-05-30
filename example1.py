import shake2py


path = './example1.shk'

#open the script and read it
f = file(path,mode='r')
data = f.read()
f.close()

#Read the script data and construct a graph
script = shake2py.Parse(data)

#the script is now graphed and ready to be manipulated

#Nodes are stored in a dictionary as Node Objects

#parameters are always strings, I have no way of detecting the parameters type,
#so strings must always be quoted, floats and int and expressions don't need quotes
#to see a nodes parameters

print "Image Node Parameters:", script['Image'].parameters

#to see a node Type

print "Image Node NodeType:", script['Image'].nodeType

#to get nodes input node names

print "Blur Input Nodes:", script['Blur1'].getInputNodeNames()

#to see what parameter index has that input

input_nodes = script['Blur1'].getInputNodeNames()

print input_nodes[0],"plugged in on input:", script['Blur1'].inputs[input_nodes[0]]

#to modify a nodes parameters you must know the index of the parameter you want to modify
#to find out the index look at the shake docs for that type of node
#example add more blur, please not that its a good idea for it to be a string

print "blur amount was ", script['Blur1'].parameters[1] 
script['Blur1'].parameters[1] ='10'
print "blur amount now is", script['Blur1'].parameters[1] 


#script globals are in a dictionary 

print "SCRIPT GLOBALS:"
for key,value in script.globals.items():
    print "   ",key,'=',value


#to change a value of something in the scripts globals

print "TimeRange was ",script.globals['TimeRange']
script.globals['TimeRange'] = '1-100'
print "TimeRange now is ",script.globals['TimeRange']

#to save the script

new_script = script.dump()
save_path = './example_output.shk'

print "saving script to",save_path
f = file(save_path,mode='w')
f.write(new_script)
f.close()

print 'saved.'



