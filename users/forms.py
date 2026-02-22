from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from courses.models import Course, Lesson, Profile

# --- NEW SIGNUP FORM ---
class UserSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Use your real Gmail for password recovery.")
    
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        widget=forms.RadioSelect, 
        initial='student',
        help_text="Choose 'Teacher' if you want to create and sell courses."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Vro, this email is already registered! Use a different one.")
        return email

# --- FIXED: Teacher Application Form ---
class TeacherApplicationForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'certificate']
        widgets = {
            # FIXED: Changed forms.TextField to forms.Textarea
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Tell us about your teaching experience...', 
                'rows': 4
            }),
            'certificate': forms.FileInput(attrs={'class': 'form-control'}),
        }

# --- YOUR EXISTING FORMS ---
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell students what they will learn...'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video_file', 'notes_pdf', 'duration', 'order']
        widgets = {
            'video_file': forms.FileInput(attrs={'accept': 'video/mp4'}),
            'duration': forms.TextInput(attrs={'placeholder': 'e.g. 12:30'}),
        }