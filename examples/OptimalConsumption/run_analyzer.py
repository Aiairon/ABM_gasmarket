import sys
import numpy as np
sys.path.append("../..")
from config import config
from model.analyzer import OptimalConsumptionAnalyzer

if __name__ == "__main__":
    ana = OptimalConsumptionAnalyzer(config)
    ana.run()


