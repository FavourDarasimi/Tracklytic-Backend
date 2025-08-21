from Tracker.models import SavingPlan, Category, CategorySpendingLimit, GeneralSpendingLimit,RecurringTransaction
from .utils import validate_category_exists, validate_saving_plan_exists


class TransactionService:
    
    # Service class for handling transaction-related business logic
    
    
    @staticmethod
    def process_transaction_data(data, user):
        
        #Process and validate transaction data
        
        category_id = data.get('category')
        savings_id = data.get('savings')
        
        # Validate category
        category, category_error = validate_category_exists(category_id, user)
        if category_error:
            return None, category_error
            
        # Validate saving plan
        saving = None
        if savings_id:
            saving, saving_error = validate_saving_plan_exists(savings_id, user)
            if saving_error:
                return None, saving_error
            
        return {
            'category': category,
            'saving': saving
        }, None
    
    @staticmethod
    def determine_savings_note(saving, savings_percentage, transaction_type, add_savings):
        
        #Determine the appropriate savings note based on transaction conditions
        
        if (saving.savings_reached_amount >= saving.savings_amount and 
            transaction_type == 'Credit' and add_savings):
            return 'Saving Goal Reached so no amount will be deducted'
        
        elif (saving.savings_reached_amount < saving.savings_amount and 
              saving.status == "Past Deadline" and 
              transaction_type == 'Credit' and add_savings):
            return 'Saving plan is Past the deadline, So no Percentage deducted'
        
        elif transaction_type == 'Debit' and add_savings == False:
            return 'You are making an Expense or add savings is False'
        
        else:
            return f'{savings_percentage}% has been deducted from this Credit Transaction'

    @staticmethod
    def create_recurring_transaction(data, user, category,amount,transaction):
        # Create a recurring transaction based on the provided data
        frequency = data.get('frequency')
        next_due_date = data.get('next_due_date')
        end_date = data.get('end_date')
        # Handle recurring transactions
        RecurringTransaction.objects.create(
            user=user,
            category=category,
            transaction=transaction,
            frequency=frequency,
            amount=amount,
            next_due_date=next_due_date,
            end_date=end_date,
            active=True
        )
        return "Recurring transaction created successfully"


class SavingPlanService:
    
    #Service class for handling saving plan-related business logic
    
    
    @staticmethod
    def update_saving_plan_status(saving_plan):
        
        #Update the status of a saving plan based on current conditions
     
        from datetime import date
        today = date.today()
        
        if (saving_plan.deadline is not None and 
            saving_plan.deadline < today and 
            saving_plan.status != "Completed"):
            saving_plan.savings_reached = False
            saving_plan.status = "Past Deadline"
        
        elif (saving_plan.savings_reached and 
              saving_plan.savings_reached_amount == saving_plan.savings_amount or 
              saving_plan.savings_reached_amount == saving_plan.savings_amount):
            saving_plan.savings_reached = True
            saving_plan.status = "Completed"
        
        elif saving_plan.savings_reached_amount < saving_plan.savings_amount:
            saving_plan.savings_reached = False
            saving_plan.status = "Active"
        
        saving_plan.save()
        return saving_plan
    
    @staticmethod
    def renew_saving_plan(saving_plan, new_amount):
      
        #Renew a saving plan with a new amount
       
        from datetime import date
        today = date.today()
        
        if new_amount < saving_plan.savings_reached_amount:
            return False, 'Your Saving Plan Amount Cannot be lower that the Amount you have saved'
        
        saving_plan.savings_amount = new_amount
        
        if new_amount == saving_plan.savings_reached_amount:
            saving_plan.savings_reached = True
            saving_plan.status = "Completed"
        
        elif new_amount > saving_plan.savings_reached_amount:
            saving_plan.savings_reached = False
            if saving_plan.deadline < today:
                saving_plan.status = "Past Deadline"
            elif saving_plan.deadline > today:
                saving_plan.status = "Active"
        
        saving_plan.save()
        return True, 'Saving Plan Renewed'


class BudgetService:
   
    #Service class for handling budget-related business logic
  
    
    @staticmethod
    def check_general_budget_exists(user):
       
        #Check if user already has a general budget
       
        try:
            budget = GeneralSpendingLimit.objects.get(user=user)
            return True, f'User already has a {budget.budget_plan} General Budget'
        except GeneralSpendingLimit.DoesNotExist:
            return False, None
    
    @staticmethod
    def check_category_budget_exists(category_id, user):
       
        #Check if a category already has a budget
       
        try:
            category_budget = CategorySpendingLimit.objects.get(
                category_id=category_id, 
                user=user
            )
            category = Category.objects.get(id=category_id, user=user)
            return True, f'{category.name} Category already has a budget'
        except CategorySpendingLimit.DoesNotExist:
            return False, None
    
    @staticmethod
    def get_general_limit_status(user):
        
        #Get the general spending limit status for a user
        
        from datetime import datetime, timedelta, date
        from Tracker.models import Transaction
        
        try:
            general_limit = GeneralSpendingLimit.objects.get(user=user)
            current_month = datetime.now().month
            current_year = datetime.now().year

            if general_limit.budget_plan == 'Monthly':
                monthly_transaction = Transaction.objects.filter(
                    user=user,
                    type='Debit',
                    date__month=current_month,
                    date__year=current_year
                )
                cost = sum(transaction.amount for transaction in monthly_transaction)
                
                if cost >= general_limit.budget_amount:
                    return 'Your Monthly Limit has been Reached'
                else:
                    total = general_limit.budget_amount - cost
                    return f'{total} remaining to reach your Monthly Limit'
                    
            elif general_limit.budget_plan == 'Weekly':
                today = date.today()
                start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)  # Sunday
                end_of_week = start_of_week + timedelta(days=6)  # Saturday

                weekly_transactions = Transaction.objects.filter(
                    user=user,
                    type='Debit',
                    date__gte=start_of_week,
                    date__lte=end_of_week
                )
                cost = sum(transaction.amount for transaction in weekly_transactions)
                
                if cost >= general_limit.budget_amount:
                    return 'Your Weekly Limit has been Reached'
                else:
                    total = general_limit.budget_amount - cost
                    return f'{total} remaining to reach your Weekly Limit'
                    
            elif general_limit.budget_plan == 'Daily':
                today = date.today()
                today_transactions = Transaction.objects.filter(
                    user=user,
                    type='Debit',
                    date__date=today
                )
                cost = sum(transaction.amount for transaction in today_transactions)
                
                if cost >= general_limit.budget_amount:
                    return 'Your Daily Limit has been Reached'
                else:
                    total = general_limit.budget_amount - cost
                    return f'{total} remaining to reach your Daily Limit'
                    
            return None
        except GeneralSpendingLimit.DoesNotExist:
            return 'User does not have a general spending limit'


class SavingsService:
    
    # Service class for handling savings-related business logics
    
    
    @staticmethod
    def process_savings_from_income(transaction):
        """
        Process savings from income transaction
        """
        add_savings = transaction.add_savings
        savings_percentage = transaction.savings_percentage
        transaction_type = transaction.type
        
        if transaction_type == 'Credit' and add_savings:
            savings_id = transaction.savings.id
            savings = SavingPlan.objects.get(id=savings_id)
            
            if savings.status == "Active":
                percentage_amount = transaction.amount * (savings_percentage / 100)
                savings.savings_reached_amount += percentage_amount
                savings.save()
                
                if savings.savings_reached_amount == savings.savings_amount:
                    savings.savings_reached = True
                    savings.save()
                    return f'{savings.name} saving goal reached'
                    
                elif savings.savings_reached_amount < savings.savings_amount:
                    remaining_amount = savings.savings_amount - savings.savings_reached_amount
                    return f'{savings.name} saving goal remaining {remaining_amount} to be completed'
                    
                elif savings.savings_reached_amount > savings.savings_amount:
                    savings.savings_reached = True
                    savings.save()
                    add_ons = savings.savings_reached_amount - savings.savings_amount
                    savings.savings_reached_amount -= add_ons
                    return f'{savings.name} saving goal reached and {add_ons} added back to the transaction amount'
                    
            elif savings.status == "Past Deadline":
                return 'Saving plan is Past the deadline, Renew to continue saving'
                
            elif savings.status == "Completed":
                return f'{savings.name} Saving Plan goal reached'
                
            savings.save()
            return None
            
        return 'You are making an Expense or add savings is False'
