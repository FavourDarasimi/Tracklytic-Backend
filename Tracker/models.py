from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

user = get_user_model()

Type = (
    ("Expense","Expense"),
    ("Income","Income"),
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
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=Category_Type)
    tag = models.CharField(max_length=100, null=True, blank=True)
    is_system = models.BooleanField(default=False)
    icon = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(
                fields=['user','type']
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user','name'],
                name='unique_user_category_name'
            )
        ]

    


# class SubCategory(models.Model):
#     user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     name =  models.CharField(max_length=100)
#     tag = models.CharField(max_length=100,null=True,blank=True)

#     def __str__(self):
#         return f'{self.category.tag}__{self.name}'


class GeneralSpendingLimit(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    budget_plan = models.CharField(choices=Plan,max_length=100,blank=True)
    budget_amount = models.PositiveIntegerField()

    def __str__(self):
        return self.user.username
    
    class Meta:
        indexes = [
            models.Index(
                fields=['user','budget_plan']
            )
        ]

class CategorySpendingLimit(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True,blank=True)
    budget_plan = models.CharField(choices=Plan,max_length=100,blank=True)
    budget_amount = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.user.username} - {self.category}'
 
    class Meta:
        indexes = [
            models.Index(
                fields=['user','category']
            ),
            models.Index(
                fields=['user','budget_plan']
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user','category','budget_plan'],
                name='unique_user_category_spending_limit'
            )
        ]

class SavingPlan(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100)
    savings_amount = models.PositiveIntegerField()
    savings_reached_amount = models.PositiveIntegerField(default=0)
    savings_reached = models.BooleanField(default=False)
    deadline = models.DateField(null=True,blank=True)
    status = models.CharField(choices=Saving_Plan_Status,max_length=100,null=True,blank=True)

    def __str__(self):
        return f'{self.user.username} {self.name} savings'
    
    class Meta:
        indexes = [
            models.Index(
                fields=['user','status']
            ),
            models.Index(
                fields=['deadline']
            )
        ]


class Transaction(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    party_name = models.CharField(max_length=200,null=True,blank=True)
    amount = models.PositiveIntegerField(null=True,blank=True)
    type = models.CharField(choices=Type,max_length=50,null=True,blank=True)
    category= models.ForeignKey(Category, on_delete=models.CASCADE,null=True,blank=True)
    notes = models.TextField(max_length=500,blank=True,null=True)
    receipt = models.FileField(upload_to="receipts/",blank=True,null=True)
    transaction_date = models.DateTimeField(null=True, blank=True,default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    add_savings = models.BooleanField(default=False)
    savings_percentage = models.PositiveIntegerField(null=True,blank=True)
    savings = models.ForeignKey(SavingPlan,on_delete=models.CASCADE,null=True,blank=True)
    savings_note = models.TextField(max_length=500,blank=True,null=True)
    recurring = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    

    def __str__(self):
        return f'{self.user.username} - {self.type} - {self.party_name}'
    
    class Meta:
        indexes = [
            models.Index(
                fields=['user','transaction_date']
            ),
            models.Index(
                fields=['user','category']
            ),
            models.Index(
                fields=['is_deleted']
            )
        ]
    

class RecurringTransaction(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=[('Daily', 'Daily'), ('Weekly', 'Weekly'), ('Monthly', 'Monthly'), ('Yearly', 'Yearly')])
    next_due_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    

    
    class Meta:
        indexes = [
            models.Index(
                fields=['user','active']
            ),
            models.Index(
                fields=['next_due_date']
            )
        ]
    
# Create your models here.
