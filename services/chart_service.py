import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_dashboard(analytics_data: dict) -> bytes:
    """
    Generates a Matplotlib dashboard image (.png) from analytics data.
    """
    # Use a dark, modern theme
    plt.style.use("dark_background")
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 10))
    fig.suptitle('Performance Dashboard', fontsize=20, fontweight='bold', color='white', y=0.98)
    fig.patch.set_facecolor('#0a0b10')  # Match UI bg-primary
    
    # Optional: adjust subplot axes background
    for ax in axes:
        ax.set_facecolor('#13141c') # bg-secondary
        ax.grid(color='#2D3748', linestyle='--', linewidth=0.5, alpha=0.5)

    campaigns = analytics_data.get("campaigns", [])
    if not campaigns:
        axes[0].text(0.5, 0.5, "No Active Campaigns", ha='center', va='center', fontsize=16)
        axes[1].text(0.5, 0.5, "No Active Campaigns", ha='center', va='center', fontsize=16)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # --- Plot 1: Revenue vs Spend (Bar Chart) ---
    ax1 = axes[0]
    names = [c["campaign_name"][:15] + '...' if len(c["campaign_name"]) > 15 else c["campaign_name"] for c in campaigns]
    revenues = [c["revenue"] for c in campaigns]
    spends = [c["ad_spend"] for c in campaigns]
    
    x = range(len(names))
    width = 0.35

    ax1.bar([i - width/2 for i in x], spends, width, label='Ad Spend', color='#f59e0b')
    ax1.bar([i + width/2 for i in x], revenues, width, label='Revenue', color='#10b981')
    
    ax1.set_ylabel('Amount ($)', fontsize=12)
    ax1.set_title('Revenue vs Ad Spend by Campaign', fontsize=14, color='white', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    ax1.legend()

    # --- Plot 2: True ROAS vs Profit Margin (Scatter) ---
    ax2 = axes[1]
    roas_vals = [c["true_roas"] for c in campaigns]
    margins = [c["profit_margin"] for c in campaigns]
    profits = [c["profit"] for c in campaigns]
    
    # Map colors based on profit (Green > 0, Red < 0, Gray 0)
    colors = ['#10b981' if p > 0 else '#ef4444' if p < 0 else '#6b7280' for p in profits]

    ax2.scatter(margins, roas_vals, s=150, c=colors, alpha=0.8, edgecolors="white", linewidths=1)
    
    for i, name in enumerate(names):
        ax2.annotate(name, (margins[i], roas_vals[i]), xytext=(5, 5), textcoords='offset points', fontsize=9, color='lightgray')

    ax2.set_xlabel('Profit Margin (%)', fontsize=12)
    ax2.set_ylabel('True ROAS', fontsize=12)
    ax2.set_title('Campaign Efficiency (ROAS vs Margin)', fontsize=14, color='white', pad=15)

    # 0 baseline references
    ax2.axhline(0, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    ax2.axvline(0, color='gray', linestyle='-', linewidth=1, alpha=0.3)

    plt.tight_layout(pad=3.0)
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    
    return buf.getvalue()
