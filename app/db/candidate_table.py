from tortoise import fields, models

class Candidate(models.Model):
    id = fields.IntField(pk=True)
    

    name = fields.CharField(max_length=50, null=True)
    phone = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=100, null=True)
    
    avatar_url = fields.CharField(max_length=255, null=True)

    resume = fields.ForeignKeyField('models.Resume', related_name='candidate')
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "candidates"