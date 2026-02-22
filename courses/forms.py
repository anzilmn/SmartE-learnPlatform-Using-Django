from django import forms
from django.contrib.auth.models import User
from .models import Profile, Course 

# --- USER & PROFILE FORMS ---
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control rounded-3', 
                'rows': 4, 
                'placeholder': 'Tell us about your skills, vro...'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

# --- COURSE EDIT FORM (Publish Removed) ---
class CourseEditForm(forms.ModelForm):
    class Meta:
        model = Course
        # Removed 'is_published' from here
        fields = ['title', 'description', 'price', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'Enter course title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-3', 
                'rows': 4,
                'placeholder': 'What will students learn?'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'Set price in ₹'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control rounded-3'
            }),
        }



from django import forms
from .models import SupportTicket

class AdminReplyForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['admin_reply', 'is_resolved']
        widgets = {
            'admin_reply': forms.Textarea(attrs={
                'class': 'form-control rounded-4',
                'placeholder': 'Write your solution here...',
                'rows': 5
            }),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }