from flask import Flask, render_template, request, jsonify
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for generating images
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Define tax rates for different provinces
TAX_RATES = {
    'Ontario': {'employee': 0.4341, 'freelance': 0.4341},
    'British Columbia': {'employee': 0.4370, 'freelance': 0.4370},
    'Alberta': {'employee': 0.3800, 'freelance': 0.3800},
    'Quebec': {'employee': 0.4997, 'freelance': 0.4997},
    'Nova Scotia': {'employee': 0.4750, 'freelance': 0.4750},
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        # Get form inputs with validation
        province = request.form.get('province')
        salary = float(request.form.get('salary', 0))
        freelance_rate = float(request.form.get('freelance_rate', 0))
        hours_per_week = float(request.form.get('hours_per_week', 0))
        weeks_per_year = float(request.form.get('weeks_per_year', 0))

        if not province or salary <= 0 or freelance_rate <= 0 or hours_per_week <= 0 or weeks_per_year <= 0:
            raise ValueError("Invalid input values")

        # Perform calculations
        results = calculate_income(salary, freelance_rate, hours_per_week, weeks_per_year, province)
        
        # Generate comparison chart
        chart = generate_comparison_chart(results)

        return jsonify(resultsTable=results['table'], summary=results['summary'], chart=chart)
    except ValueError as e:
        return jsonify(error=str(e)), 400

def calculate_income(salary, freelance_rate, hours_per_week, weeks_per_year, province):
    """Calculates the income, taxes, and required hours for both employee and freelancer."""
    # Calculate annual income for freelance
    freelance_income = freelance_rate * hours_per_week * weeks_per_year

    # Get tax rates for the selected province
    employee_tax_rate = TAX_RATES[province]['employee']
    freelance_tax_rate = TAX_RATES[province]['freelance']

    # Calculate taxes
    employee_tax = salary * employee_tax_rate
    freelance_tax = freelance_income * freelance_tax_rate

    # Calculate net income
    employee_net_income = salary - employee_tax
    freelance_net_income = freelance_income - freelance_tax

    # Calculate required hours to match employee net income
    required_hours = (employee_net_income + freelance_tax) / freelance_rate

    # Prepare results for JSON response
    results_table = f"""
    <tr><td>Gross Income</td><td>{format_currency(salary)}</td><td>{format_currency(freelance_income)}</td></tr>
    <tr><td>Tax Rate</td><td>{employee_tax_rate:.2%}</td><td>{freelance_tax_rate:.2%}</td></tr>
    <tr><td>Tax Paid</td><td>{format_currency(employee_tax)}</td><td>{format_currency(freelance_tax)}</td></tr>
    <tr><td>Net Income</td><td>{format_currency(employee_net_income)}</td><td>{format_currency(freelance_net_income)}</td></tr>
    <tr><td>Required Hours to Match Employee Net Income</td><td colspan="2">{required_hours:.2f} hours</td></tr>
    """

    summary = (f"As an employee, your gross income is {format_currency(salary)} with a net income of "
               f"{format_currency(employee_net_income)} after paying {format_currency(employee_tax)} in taxes. "
               f"As a freelancer, your gross income is {format_currency(freelance_income)} with a net income of "
               f"{format_currency(freelance_net_income)} after paying {format_currency(freelance_tax)} in taxes. "
               f"To match the employee's net income, a freelancer would need to work {required_hours:.2f} hours per year.")

    if required_hours > (hours_per_week * weeks_per_year):
        summary += " Warning: The freelancer would need to work more hours than currently specified to match the employee's net income."
    else:
        summary += " The freelancer can match or exceed the employee's net income within the specified working hours."

    return {
        "table": results_table,
        "summary": summary,
        "employee": {
            "gross_income": salary,
            "net_income": employee_net_income,
            "tax_paid": employee_tax
        },
        "freelance": {
            "gross_income": freelance_income,
            "net_income": freelance_net_income,
            "tax_paid": freelance_tax
        }
    }

def format_currency(value):
    """Format a number as currency with commas and two decimal places."""
    return f"${value:,.2f}"

def generate_comparison_chart(results):
    """Generate a bar chart comparing employee and freelancer incomes."""
    categories = ['Gross Income', 'Net Income', 'Tax Paid']
    employee_values = [results['employee']['gross_income'], results['employee']['net_income'], results['employee']['tax_paid']]
    freelance_values = [results['freelance']['gross_income'], results['freelance']['net_income'], results['freelance']['tax_paid']]

    x = range(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width/2 for i in x], employee_values, width, label='Employee', color='#4e79a7')
    ax.bar([i + width/2 for i in x], freelance_values, width, label='Freelancer', color='#f28e2b')

    ax.set_ylabel('Amount ($)')
    ax.set_title('Employee vs Freelancer Income Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()

    # Format y-axis labels as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))

    # Adjust layout and save to base64
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    chart = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return chart

if __name__ == '__main__':
    app.run(debug=True)