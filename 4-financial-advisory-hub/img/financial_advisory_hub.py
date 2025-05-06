import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Set background color
ax.set_facecolor('#f5f5f5')
fig.patch.set_facecolor('#f5f5f5')

# Define colors
main_color = '#0066cc'
sub_agent1_color = '#009933'
sub_agent2_color = '#cc6600'
arrow_color = '#666666'
text_color = '#333333'

# Create main agent box
main_agent = patches.Rectangle((3, 4), 4, 2, linewidth=2, edgecolor=main_color, facecolor='white', alpha=0.9)
ax.add_patch(main_agent)

# Create sub-agent boxes
sub_agent1 = patches.Rectangle((1, 1), 3, 2, linewidth=2, edgecolor=sub_agent1_color, facecolor='white', alpha=0.9)
ax.add_patch(sub_agent1)
sub_agent2 = patches.Rectangle((6, 1), 3, 2, linewidth=2, edgecolor=sub_agent2_color, facecolor='white', alpha=0.9)
ax.add_patch(sub_agent2)

# Create user box
user = patches.Rectangle((3, 7), 4, 1.5, linewidth=2, edgecolor=arrow_color, facecolor='white', alpha=0.9)
ax.add_patch(user)

# Add arrows
arrow_props = dict(arrowstyle='->', linewidth=2, color=arrow_color)
ax.annotate('', xy=(5, 4), xytext=(5, 7), arrowprops=arrow_props)
ax.annotate('', xy=(2.5, 3), xytext=(4, 4), arrowprops=arrow_props)
ax.annotate('', xy=(7.5, 3), xytext=(6, 4), arrowprops=arrow_props)

# Add text
ax.text(5, 5, 'Financial Advisory Hub\n(Supervisor Agent)', ha='center', va='center', fontsize=12, fontweight='bold', color=text_color)
ax.text(2.5, 2, 'Data Analytics Agent\n(Transaction Analysis)', ha='center', va='center', fontsize=10, fontweight='bold', color=text_color)
ax.text(7.5, 2, 'Customer Insights Agent\n(Visualization Explanation)', ha='center', va='center', fontsize=10, fontweight='bold', color=text_color)
ax.text(5, 7.75, 'User / Bank Operator', ha='center', va='center', fontsize=12, fontweight='bold', color=text_color)

# Set limits and remove axes
ax.set_xlim(0, 10)
ax.set_ylim(0, 9)
ax.axis('off')

# Add title
plt.title('Financial Advisory Hub Architecture', fontsize=14, fontweight='bold', pad=20, color=text_color)

# Save the figure
plt.savefig('img/financial_advisory_hub.png', dpi=300, bbox_inches='tight')
plt.close()

print("Architecture diagram created and saved to img/financial_advisory_hub.png")
