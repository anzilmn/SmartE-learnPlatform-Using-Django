import uuid
import time  # Required for the timer logic
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, Question, Choice, QuizResult 
from courses.models import Certificate, Enrollment, LessonCompletion
import time
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, Question, Choice, QuizResult
from courses.models import Course, Enrollment, LessonCompletion
 
@login_required
def take_quiz(request, quiz_id):
    import time
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    from .models import Quiz, QuizResult, Choice 
    from courses.models import Enrollment, LessonCompletion

    # VRO: prefetch_related ensures ALL questions and choices load!
    quiz = get_object_or_404(
        Quiz.objects.prefetch_related('questions__choices'), 
        id=quiz_id
    )
    course = quiz.course
    questions = quiz.questions.all()

    # --- 1. SECURITY & STATUS CHECK ---
    enrollment = Enrollment.objects.filter(
        user=request.user, 
        course=course, 
        status__in=['approved', 'finished']
    ).first()

    if not enrollment:
        messages.error(request, "Vro, you must be enrolled to take the quiz!")
        return redirect('course_detail', course_id=course.id)

    # 🚨 VRO BLOCK: If they already finished, don't let them in!
    if enrollment.status == 'finished':
        messages.info(request, "Vro, you already finished this section! 🎓")
        return redirect('course_detail', course_id=course.id)

    # --- 2. PROGRESS CHECK ---
    # Only runs for 'approved' students because 'finished' students were blocked above
    total_lessons = course.lessons.count()
    completed_lessons = LessonCompletion.objects.filter(user=request.user, lesson__course=course).count()
    
    if completed_lessons < total_lessons:
        messages.warning(request, "Finish all lessons before the final exam, vro! 📚")
        return redirect('course_detail', course_id=course.id)

    # --- 3. TIMER LOGIC ---
    session_key = f'quiz_start_time_{quiz.id}'
    current_time = int(time.time())
    
    if session_key not in request.session:
        request.session[session_key] = current_time
        start_time = current_time
    else:
        start_time = request.session[session_key]

    seconds_elapsed = current_time - start_time
    total_seconds_allowed = quiz.time_limit * 60
    remaining_seconds = total_seconds_allowed - seconds_elapsed

    if remaining_seconds <= 0 and request.method == "GET":
        if session_key in request.session:
            del request.session[session_key]
        messages.error(request, "Vro, your time ran out!")
        return redirect('course_detail', course_id=course.id)

    # --- 4. HANDLING SUBMISSION ---
    if request.method == "POST":
        # Grace period check
        if remaining_seconds < -10: 
            if session_key in request.session:
                del request.session[session_key]
            messages.error(request, "Submission failed: Time limit exceeded.")
            return redirect('course_detail', course_id=course.id)

        score = 0
        total_questions = questions.count()

        for question in questions:
            selected_choice_id = request.POST.get(f"question_{question.id}")
            if selected_choice_id:
                try:
                    selected_choice = Choice.objects.get(id=selected_choice_id)
                    if selected_choice.is_correct:
                        score += 1
                except Choice.DoesNotExist:
                    continue
        
        percentage = int((score / total_questions) * 100) if total_questions > 0 else 0
        passed = percentage >= quiz.pass_score

        # Save or update the result
        QuizResult.objects.update_or_create(
            user=request.user,
            quiz=quiz,
            defaults={'score': score, 'percentage': percentage, 'passed': passed}
        )

        # Clear session timer
        if session_key in request.session:
            del request.session[session_key]

        if passed:
            messages.success(request, f"MASSIVE WORK, VRO! You passed with {percentage}%! 🚀")
            messages.info(request, "One last step: Upload your final project to claim your certificate! 🎓")
            return redirect('course_detail', course_id=course.id)
        
        else:
            return render(request, 'quizzes/quiz_result.html', {
                'quiz': quiz,
                'score': score,
                'total': total_questions,
                'percentage': percentage,
                'passed': passed
            })

    return render(request, 'quizzes/take_quiz.html', {
        'quiz': quiz, 
        'questions': questions,
        'remaining_seconds': remaining_seconds,
        'is_finished': False
    })


from django.shortcuts import render, redirect, get_object_or_404
from .forms import QuizForm, QuestionForm, ChoiceFormSet
from courses.models import Course

def create_quiz(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == "POST":
        quiz_form = QuizForm(request.POST)
        if quiz_form.is_valid():
            quiz = quiz_form.save(commit=False)
            quiz.course = course
            quiz.save()
            # VRO: This redirects to the Question Adding page!
            return redirect('add_question', quiz_id=quiz.id)
    else:
        quiz_form = QuizForm()
        
    return render(request, 'quizzes/create_quiz.html', {'quiz_form': quiz_form, 'course': course})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Question, Choice
from .forms import QuizForm # Your existing form

def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == "POST":
        question_text = request.POST.get('question_text')
        question = Question.objects.create(quiz=quiz, text=question_text)
        
        # Get choices and the correct answer index from the form
        for i in range(1, 5):
            choice_text = request.POST.get(f'choice_{i}')
            is_correct = (request.POST.get('correct_choice') == str(i))
            if choice_text:
                Choice.objects.create(question=question, text=choice_text, is_correct=is_correct)
        
        messages.success(request, "Question added successfully! Add another or finish.")
        return redirect('add_question', quiz_id=quiz.id)

    return render(request, 'quizzes/add_question.html', {'quiz': quiz})





from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Course, Question # Adjust based on your model names
from django.contrib import messages

@login_required
def manage_questions(request, course_id):
    # 1. Get the course first
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # 2. Try to get the quiz, if it doesn't exist, CREATE IT on the fly
    quiz, created = Quiz.objects.get_or_create(
        course=course,
        defaults={'title': f"Quiz for {course.title}"}
    )
    
    # 3. Get existing questions
    questions = quiz.questions.all().prefetch_related('choices')

    if request.method == "POST":
        question_text = request.POST.get('question_text')
        correct_index = request.POST.get('correct_choice') 
        
        if question_text and correct_index:
            question = Question.objects.create(quiz=quiz, text=question_text)
            
            for i in range(1, 5):
                choice_text = request.POST.get(f'choice_{i}')
                if choice_text:
                    Choice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=(str(i) == correct_index)
                    )
            
            messages.success(request, "Question added successfully!")
            return redirect('manage_questions', course_id=course_id)

    return render(request, 'quizzes/manage_questions.html', {
        'quiz': quiz,
        'questions': questions,
        'course': course
    })



@login_required
def edit_question(request, question_id):
    # Security check: Ensure instructor owns the course this question belongs to
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    course = question.quiz.course

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Question and choices updated successfully!")
            return redirect('manage_questions', course_id=course.id)
    else:
        form = QuestionForm(instance=question)
        # Load existing choices into the formset
        formset = ChoiceFormSet(instance=question)

    return render(request, 'quizzes/edit_question.html', {
        'form': form,
        'formset': formset,
        'course': course,
        'question': question
    })

@login_required
def delete_question(request, question_id):
    # FIXED: Added 'quiz__' before course to follow the relationship chain
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    course_id = question.quiz.course.id
    question.delete()
    messages.success(request, "Question deleted successfully, vro!")
    return redirect('manage_questions', course_id=course_id)



from courses.models import Review


from courses.models import Review, Enrollment, Course # Make sure Course and Enrollment are imported

@login_required
def submit_review(request, course_id):
    if request.method == "POST":
        course = get_object_or_404(Course, id=course_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating:
            messages.error(request, "Please provide a rating before submitting! ⭐")
            return redirect(request.META.get('HTTP_REFERER', 'course_list'))

        # Save or update the review
        Review.objects.update_or_create(
            course=course, user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        
        messages.success(request, "Thanks for the feedback, vro! Check out your next challenge below. 🎓")
        
        # 🔥 NEW: Recommendation Logic 🔥
        # Get IDs of courses user is already in
        user_enrolled_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        
        # Get 3 random courses the user is NOT enrolled in
        recommended_courses = Course.objects.exclude(id__in=user_enrolled_ids).order_by('?')[:3]
        
        # Redirect to a new "Success & Recommendations" page
        return render(request, 'quizzes/quiz_success_recs.html', {
            'course': course,
            'recommended': recommended_courses
        })

    return redirect('course_list') 