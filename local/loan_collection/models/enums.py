from odoo import _

# Gender
GENDER = [  
    ('1', 'male'),  
    ('2', 'female')  
]  

# Education  
EDUCATION = [  
    ('1', 'Secondary School'),  
    ('2', 'High School'),  
    ('3', 'Diploma'),  
    ('4', 'Bachelors'),  
    ('5', 'Masters'),  
    ('6', 'Doctorate')  
]  

# Marital Status  
MARITAL_STATUS = [  
    ('1', 'Single'),  
    ('2', 'Married'),  
    ('3', 'Secrecy')  
]  

# House Status  
HOUSE_STATUS = [  
    ('1', 'Rented'),  
    ('2', 'Office Provided'),  
    ('3', 'Owned'),  
    ('99', 'Others')  
]  

# Children Count  
CHILDREN_COUNT = [  
    ('0', '0'),  
    ('1', '1'),  
    ('2', '2'),  
    ('3', '3'),  
    ('4', 'More')  
]  

# Occupation  
OCCUPATION = [  
    ('0', 'Unemployed'),  
    ('1', 'Self-employed'),  
    ('2', 'Salaried'),  
    ('3', 'Senior executive'),  
    ('4', 'Company manager'),  
    ('5', 'Student'),  
    ('6', 'Government'),  
    ('7', 'Servant'),  
    ('99', 'Others')  
]  

# Loan Purpose  
LOAN_PURPOSE = [  
    ('1', 'Personal Expenses'),  
    ('2', 'Household Expenses'),  
    ('3', 'Repay Credit Card Bill'),  
    ('4', 'Repay Other loans'),  
    ('5', 'Festival Function'),  
    ('6', 'Education'),  
    ('7', 'Medical Expense'),  
    ('8', 'Marriage'),  
    ('9', 'House Renovation'),  
    ('10', 'Car Purchase'),  
    ('11', 'Travel/Vacation')  
]  

# Salary  
SALARY = [  
    ('1', '0-10000'),  
    ('2', '10000-20000'),  
    ('3', '20000-30000'),  
    ('4', '30000-50000'),  
    ('5', '50000+')  
]  

# Contact Relationship  
CONTACT_RELATIONSHIP = [  
    ('1', 'Father'),  
    ('2', 'Mother'),  
    ('3', 'Spouse'),  
    ('4', 'Friend'),  
    ('5', 'Family'),  
    ('6', 'Brothers'),  
    ('7', 'Colleague'),  
    ('99', 'Others')  
]  

# Id Photo Code  
ID_PHOTO_CODE = [  
    ('0', 'None'),  
    ('1', 'PAN Card Front'),  
    ('2', 'PAN Card Back'),  
    ('3', 'ID Card Front'),  
    ('4', 'ID Card Hold')  
]  

# Contact Type  
CONTACT_TYPE = [  
    ('1', 'Primary'),  
    ('2', 'Secondary'),  
    ('99', 'Other')  
]

ORDER_TYPE = [('1', _('First-time Loan')), ('2', _('Re-Loan'))]


ORDER_STATUS = [
    ('1', _('Pending Assignment')),
    ('2', _('Allocated')),
    ('3', _('Pending Loan Release')),
    ('4', _('In the loan')),
    ('5', _('Loan Success')),
    ('6', _('Loan Failed')),
    ('7', _('Pending Repayment')),
    ('8', _('Overdue')),
    ('9', _('Settled Repayment')),
    ('99', _('Refused')),
]

AUDIT_RESULT = [
    ('1', '通过'),
    ('2', '拒绝')
]

AUDIT_REASON = [
    ('1', '无异常通过'), 
    ('2', '申请人核身失败'), 
    ('3', '联系人号码无效'),
    ('4', '申请人信息无法核实'),
    ('5', '无法联络申请人'),
    ('99', '其他')
]


FINANCIAL_ACTION = [('1', '手动放款'), ('2', '自动放款')]

FINANCIAL_RESULT = [('1', '成功'), ('2', '失败')]