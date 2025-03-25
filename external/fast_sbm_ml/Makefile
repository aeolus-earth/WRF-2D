# Compiler settings
CXX := g++
CXXFLAGS := -std=c++17 -Wall -O2

# Find PyTorch paths using python
TORCH_DIR = ${LIBTORCH}

# Additional flags for PyTorch
CXXFLAGS += -I$(TORCH_DIR)/include -L$(TORCH_DIR)/lib -ltorch -lc10 -ltorch_cpu
LDFLAGS := -L$(TORCH_DIR)/lib

# Object file paths
SRC_DIR := src/cpp
BUILD_DIR := build

# Library objects
LIB_SRCS := $(SRC_DIR)/c_fast_sbm_ml.cpp
LIB_OBJS := $(patsubst $(SRC_DIR)/%.cpp,$(BUILD_DIR)/%.o,$(LIB_SRCS))

# Driver objects
DRIVER_SRCS := $(SRC_DIR)/c_test_driver.cpp
DRIVER_OBJS := $(patsubst $(SRC_DIR)/%.cpp,$(BUILD_DIR)/%.o,$(DRIVER_SRCS))

# Targets
LIB_TARGET := $(BUILD_DIR)/libc_fast_sbm_ml.a
DRIVER_TARGET := $(BUILD_DIR)/driver

# Main targets
all: dir model $(LIB_TARGET) $(DRIVER_TARGET)

dir: 
	mkdir -p build
# Library build
$(LIB_TARGET): $(LIB_OBJS)
	ar rcs $@ $^ 

# Driver build
$(DRIVER_TARGET): $(DRIVER_OBJS) $(LIB_TARGET)
	$(CXX) -o $@ $^ $(CXXFLAGS)

# Object file compilation
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Dependencies
$(BUILD_DIR)/c_fast_sbm_ml.o: $(SRC_DIR)/c_fast_sbm_ml.cpp $(SRC_DIR)/c_fast_sbm_ml.h
$(BUILD_DIR)/c_test_driver.o: $(SRC_DIR)/c_test_driver.cpp $(SRC_DIR)/c_fast_sbm_ml.h

# Cleanup
clean:
	rm -rf $(BUILD_DIR) $(DRIVER_TARGET) $(LIB_TARGET)

superclean: clean
	
.PHONY: all dirs clean

model:
	python src/python/generate_model.py
