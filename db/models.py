from django.db import models


class User(models.Model):
    user_id = models.SmallAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    is_banned = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user"


class Menfess(models.Model):
    tweet_id = models.CharField(max_length=20, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="menfesses")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "menfess"
