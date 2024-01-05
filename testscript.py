# This actually works for programming a function!

# THIS WORKS! Just need to call inspect inside the class and pass along class reference if need be.

def new_func(self):
    print(self.threadnum)

# Test pb func()
self.func = self.default_func
self.func = new_func
self.run_program()

# print(self.new_params)

print(locals().keys())
# print(dir(self))
