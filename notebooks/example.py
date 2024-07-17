# %% [markdown]
# # Example of an interactive notebook
#
# 1. Run these notebooks as interactive scripts using the `jupyter` extension for VSCode.
# 2. Open the command palette (F1) and run `Jupyter: Create interactive window`.
# 3. Run the cells below using Ctrl+Enter.

# %% Reload the module when it changes
# !%load_ext autoreload
# !%autoreload 2
# Use python to get the current directory
from pathlib import Path

print(f"The current directory is {Path().absolute()}")

# %% Install matplotlib using pip
# !pip install matplotlib

# %% [markdown]
# ## Plot a figure
# You can inspect the figure in the interactive window.
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)
plt.plot(x, y)
