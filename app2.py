import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Initialize data storage - use a more robust approach for HF deployment
import os
transactions = []

# Predefined categories
EXPENSE_CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment", 
    "Bills & Utilities", "Healthcare", "Travel", "Education", 
    "Personal Care", "Home & Garden", "Other"
]

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Business", "Investments", 
    "Rental Income", "Gifts", "Other"
]

def add_transaction(transaction_type, category, amount, description, date):
    """Add a new transaction to the database"""
    global transactions
    
    try:
        if not amount or amount <= 0:
            return "❌ Please enter a valid amount", get_recent_transactions()
        
        if not category:
            return "❌ Please select a category", get_recent_transactions()
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return "❌ Please enter date in YYYY-MM-DD format", get_recent_transactions()
        
        transaction = {
            'id': len(transactions) + 1,
            'type': transaction_type,
            'category': category,
            'amount': float(amount),
            'description': description or "No description",
            'date': date,
            'timestamp': datetime.now().isoformat()
        }
        
        transactions.append(transaction)
        
        success_msg = f"✅ {transaction_type} of ${amount:.2f} added successfully!"
        return success_msg, get_recent_transactions()
        
    except Exception as e:
        return f"❌ Error: {str(e)}", get_recent_transactions()

def get_recent_transactions():
    """Get recent transactions for display"""
    try:
        if not transactions:
            return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])
        
        df = pd.DataFrame(transactions)
        df['Date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('timestamp', ascending=False).head(10)
        
        display_df = df[['Date', 'type', 'category', 'amount', 'description']].copy()
        display_df.columns = ['Date', 'Type', 'Category', 'Amount', 'Description']
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:.2f}")
        
        return display_df
    except Exception as e:
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])

def filter_transactions_by_period(period, start_date=None, end_date=None):
    """Filter transactions based on time period"""
    try:
        if not transactions:
            return pd.DataFrame()
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        today = datetime.now().date()
        
        if period == "Today":
            filtered_df = df[df['date'].dt.date == today]
        elif period == "This Week":
            start_week = today - timedelta(days=today.weekday())
            filtered_df = df[df['date'].dt.date >= start_week]
        elif period == "This Month":
            start_month = today.replace(day=1)
            filtered_df = df[df['date'].dt.date >= start_month]
        elif period == "This Year":
            start_year = today.replace(month=1, day=1)
            filtered_df = df[df['date'].dt.date >= start_year]
        elif period == "Custom Range":
            if start_date and end_date:
                start_date = pd.to_datetime(start_date).date()
                end_date = pd.to_datetime(end_date).date()
                filtered_df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
            else:
                filtered_df = df
        else:
            filtered_df = df
        
        return filtered_df
    except Exception as e:
        print(f"Error filtering transactions: {e}")
        return pd.DataFrame()

def create_summary_cards(period, start_date=None, end_date=None):
    """Create summary statistics"""
    df = filter_transactions_by_period(period, start_date, end_date)
    
    if df.empty:
        return "No data available for the selected period"
    
    total_income = df[df['type'] == 'Income']['amount'].sum()
    total_expenses = df[df['type'] == 'Expense']['amount'].sum()
    net_balance = total_income - total_expenses
    
    summary = f"""
    ## 📊 Financial Summary ({period})
    
    💰 **Total Income**: ${total_income:,.2f}
    
    💸 **Total Expenses**: ${total_expenses:,.2f}
    
    📈 **Net Balance**: ${net_balance:,.2f}
    
    📝 **Total Transactions**: {len(df)}
    """
    
    return summary

def create_expense_pie_chart(period, start_date=None, end_date=None):
    """Create pie chart for expense categories"""
    df = filter_transactions_by_period(period, start_date, end_date)
    expense_df = df[df['type'] == 'Expense']
    
    if expense_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No expense data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=16))
        fig.update_layout(title="Expense Distribution by Category")
        return fig
    
    category_totals = expense_df.groupby('category')['amount'].sum().reset_index()
    
    fig = px.pie(category_totals, values='amount', names='category',
                 title=f"Expense Distribution by Category ({period})",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        font=dict(size=12),
        title_font_size=16,
        height=400
    )
    
    return fig

def create_income_pie_chart(period, start_date=None, end_date=None):
    """Create pie chart for income categories"""
    df = filter_transactions_by_period(period, start_date, end_date)
    income_df = df[df['type'] == 'Income']
    
    if income_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No income data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=16))
        fig.update_layout(title="Income Distribution by Category")
        return fig
    
    category_totals = income_df.groupby('category')['amount'].sum().reset_index()
    
    fig = px.pie(category_totals, values='amount', names='category',
                 title=f"Income Distribution by Category ({period})",
                 color_discrete_sequence=px.colors.qualitative.Pastel1)
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        font=dict(size=12),
        title_font_size=16,
        height=400
    )
    
    return fig

def create_trend_chart(period, start_date=None, end_date=None):
    """Create line chart showing trends over time"""
    df = filter_transactions_by_period(period, start_date, end_date)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for trend analysis", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=16))
        fig.update_layout(title="Income vs Expenses Trend")
        return fig
    
    # Group by date and type
    daily_totals = df.groupby([df['date'].dt.date, 'type'])['amount'].sum().reset_index()
    daily_totals['date'] = pd.to_datetime(daily_totals['date'])
    
    fig = go.Figure()
    
    for transaction_type in ['Income', 'Expense']:
        type_data = daily_totals[daily_totals['type'] == transaction_type]
        if not type_data.empty:
            fig.add_trace(go.Scatter(
                x=type_data['date'],
                y=type_data['amount'],
                mode='lines+markers',
                name=transaction_type,
                line=dict(width=3)
            ))
    
    fig.update_layout(
        title=f"Income vs Expenses Trend ({period})",
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_bar_chart(period, start_date=None, end_date=None):
    """Create bar chart comparing categories"""
    df = filter_transactions_by_period(period, start_date, end_date)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=16))
        fig.update_layout(title="Category Comparison")
        return fig
    
    category_totals = df.groupby(['category', 'type'])['amount'].sum().reset_index()
    
    fig = px.bar(category_totals, x='category', y='amount', color='type',
                 title=f"Category Comparison ({period})",
                 barmode='group',
                 color_discrete_map={'Income': '#2E8B57', 'Expense': '#DC143C'})
    
    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Amount ($)",
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig

def update_category_choices(transaction_type):
    """Update category dropdown based on transaction type"""
    if transaction_type == "Income":
        return gr.Dropdown(choices=INCOME_CATEGORIES, value="")
    else:
        return gr.Dropdown(choices=EXPENSE_CATEGORIES, value="")

def update_charts(period, start_date, end_date):
    """Update all charts based on selected period"""
    return (
        create_summary_cards(period, start_date, end_date),
        create_expense_pie_chart(period, start_date, end_date),
        create_income_pie_chart(period, start_date, end_date),
        create_trend_chart(period, start_date, end_date),
        create_bar_chart(period, start_date, end_date)
    )

def show_custom_date_inputs(period):
    """Show/hide custom date inputs based on period selection"""
    if period == "Custom Range":
        return gr.update(visible=True), gr.update(visible=True)
    else:
        return gr.update(visible=False), gr.update(visible=False)

# Custom CSS for attractive UI
css = """
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.gradio-container {
    max-width: 1200px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
}

.gr-button-primary {
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    border: none;
    border-radius: 25px;
    padding: 10px 25px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.gr-button-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.gr-form {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.gr-panel {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px);
}

h1, h2, h3 {
    background: linear-gradient(45deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
}
"""

# Create Gradio interface
with gr.Blocks(css=css, title="💰 Expense Tracker", theme=gr.themes.Soft()) as app:
    gr.HTML("<h1 style='text-align: center; margin-bottom: 30px;'>💰 Personal Expense Tracker</h1>")
    
    with gr.Tabs():
        # Add Transaction Tab
        with gr.Tab("➕ Add Transaction"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML("<h3>💳 Add New Transaction</h3>")
                    
                    transaction_type = gr.Radio(
                        choices=["Expense", "Income"], 
                        label="Transaction Type", 
                        value="Expense"
                    )
                    
                    category = gr.Dropdown(
                        choices=EXPENSE_CATEGORIES,
                        label="Category",
                        interactive=True
                    )
                    
                    amount = gr.Number(
                        label="Amount ($)",
                        minimum=0.01,
                        step=0.01
                    )
                    
                    description = gr.Textbox(
                        label="Description (Optional)",
                        placeholder="Enter description..."
                    )
                    
                    date = gr.Textbox(
                        label="Date (YYYY-MM-DD)",
                        value=datetime.now().strftime("%Y-%m-%d"),
                        placeholder="2024-01-01"
                    )
                    
                    add_btn = gr.Button("Add Transaction", variant="primary", size="lg")
                    
                    status_msg = gr.Markdown("Ready to add transactions!")
                
                with gr.Column(scale=1):
                    gr.HTML("<h3>📋 Recent Transactions</h3>")
                    recent_transactions = gr.Dataframe(
                        value=get_recent_transactions(),
                        headers=["Date", "Type", "Category", "Amount", "Description"],
                        interactive=False
                    )
        
        # Dashboard Tab
        with gr.Tab("📊 Dashboard"):
            with gr.Row():
                period_selector = gr.Dropdown(
                    choices=["Today", "This Week", "This Month", "This Year", "Custom Range"],
                    value="This Month",
                    label="Time Period"
                )
                
                with gr.Column(visible=False) as custom_start:
                    start_date_input = gr.Textbox(label="Start Date (YYYY-MM-DD)", placeholder="2024-01-01")
                
                with gr.Column(visible=False) as custom_end:
                    end_date_input = gr.Textbox(label="End Date (YYYY-MM-DD)", placeholder="2024-12-31")
            
            summary_cards = gr.Markdown(create_summary_cards("This Month"))
            
            with gr.Row():
                expense_pie = gr.Plot()
                income_pie = gr.Plot()
            
            with gr.Row():
                trend_chart = gr.Plot()
            
            with gr.Row():
                bar_chart = gr.Plot()
    
    # Event handlers
    transaction_type.change(
        fn=update_category_choices,
        inputs=[transaction_type],
        outputs=[category]
    )
    
    add_btn.click(
        fn=add_transaction,
        inputs=[transaction_type, category, amount, description, date],
        outputs=[status_msg, recent_transactions]
    )
    
    period_selector.change(
        fn=show_custom_date_inputs,
        inputs=[period_selector],
        outputs=[custom_start, custom_end]
    )
    
    period_selector.change(
        fn=update_charts,
        inputs=[period_selector, start_date_input, end_date_input],
        outputs=[summary_cards, expense_pie, income_pie, trend_chart, bar_chart]
    )
    
    start_date_input.change(
        fn=update_charts,
        inputs=[period_selector, start_date_input, end_date_input],
        outputs=[summary_cards, expense_pie, income_pie, trend_chart, bar_chart]
    )
    
    end_date_input.change(
        fn=update_charts,
        inputs=[period_selector, start_date_input, end_date_input],
        outputs=[summary_cards, expense_pie, income_pie, trend_chart, bar_chart]
    )
    
    # Initialize charts on load
    app.load(
        fn=update_charts,
        inputs=[gr.State("This Month"), gr.State(None), gr.State(None)],
        outputs=[summary_cards, expense_pie, income_pie, trend_chart, bar_chart]
    )

if __name__ == "__main__":
    # Simple launch that works on most platforms
    app.launch()
