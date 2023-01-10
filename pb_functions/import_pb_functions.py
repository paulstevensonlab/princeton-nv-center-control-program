# Script to add references to all the pb functions defined in exec() into the class PulseMaster
#
dict_locals = sorted(locals().keys())

for o in dict_locals:
    # Check if the methods are defined according to the convention
    #  def pb_func_params
    #  def pb_func
    if 'pb_' in o and ((o + '_params') in dict_locals):
        # Reassign the function reference, in case of an overwriting of functions when reloading
        setattr(self, o, eval(o))
        setattr(self, o + '_params', eval(o + '_params'))
        # Check if exp_name does not already exist in PulseMaster
        exp_name = o.split('pb_')[-1]
        if exp_name not in self.pulse_list:
            self.pulse_list.append(exp_name)
        else:
            warnings.warn('Duplicate experiment: ' + o)

