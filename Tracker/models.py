from django.contrib.auth import get_user_model
from django.db import models

user = get_user_model()

Type = (
    ("Debit","Debit"),
    ("Credit","Credit"),
)

Plan = (
    ("Daily","Daily"),
    ("Weekly","Weekly"),
    ("Monthly","Monthly"),
)

Category_Type = (
    ("Income","Income"),
    ("Expense","Expense"),
)
Saving_Plan_Status = (
    ("Active","Active"),
    ("Past Deadline","Past Deadline"),
    ("Completed","Completed")
)

class Category(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100,choices=Category_Type)
    tag = models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return self.name



# class SubCategory(models.Model):
#     user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     name =  models.CharField(max_length=100)
#     tag = models.CharField(max_length=100,null=True,blank=True)

#     def __str__(self):
#         return f'{self.category.tag}__{self.name}'


class GeneralSpendingLimit(models.Model):
    user = models.OneToOneField(user, on_delete=models.CASCADE,null=True,blank=True)
    budget_plan = models.CharField(choices=Plan,max_length=100,blank=True)
    budget_amount = models.PositiveIntegerField()

    def __str__(self):
        return self.user.username

class CategorySpendingLimit(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True,blank=True)
    budget_plan = models.CharField(choices=Plan,max_length=100,blank=True)
    budget_amount = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.user.username} - {self.category}'
#day2

class SavingPlan(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100)
    savings_amount = models.PositiveIntegerField()
    savings_reached_amount = models.PositiveIntegerField(default=0)
    savings_reached = models.BooleanField(default=False)
    deadline = models.DateField(null=True,blank=True)
    status = models.CharField(choices=Saving_Plan_Status,max_length=100,null=True,blank=True)



class Transaction(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    party_name = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    type = models.CharField(choices=Type,max_length=50, blank=True)
    category= models.ForeignKey(Category, on_delete=models.CASCADE,null=True,blank=True)
    # sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE,null=True,blank=True)
    notes = models.TextField(max_length=500,blank=True,null=True)
    receipt = models.FileField(blank=True,null=True)
    date = models.DateTimeField(auto_now_add=True)
    add_savings = models.BooleanField(default=False)
    savings_percentage = models.PositiveIntegerField(null=True,blank=True)
    savings = models.ForeignKey(SavingPlan,on_delete=models.CASCADE,null=True,blank=True)
    savings_note = models.TextField(max_length=500,blank=True,null=True)
    recurring = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} - {self.type} - {self.party_name}'
    

class RecurringTransaction(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=[('Daily', 'Daily'), ('Weekly', 'Weekly'), ('Monthly', 'Monthly'), ('Yearly', 'Yearly')])
    next_due_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
# Create your models here.
