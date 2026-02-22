from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .models import ChatThread, Message
from courses.models import Course, Notification, Enrollment, Certificate
from django.utils import timezone

@login_required
def start_or_open_chat(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = request.user
    teacher = course.instructor 

    # 1. Prevent instructor from chatting with themselves
    if student == teacher:
        messages.error(request, "You cannot start a doubt session with yourself, vro.")
        return redirect('course_detail', course_id=course_id)

    # 2. Check Enrollment (Security Check)
    enrollment = Enrollment.objects.filter(user=student, course=course).first()
    
    if not enrollment:
        messages.error(request, "Vro, you need to be enrolled to ask doubts!")
        return redirect('course_detail', course_id=course_id)

    # 🔥 VRO FIX: Removed the 'finished' block so graduates can still access the chat!

    # 3. Get or Create the Chat Thread
    thread, created = ChatThread.objects.get_or_create(
        course=course,
        student=student,
        teacher=teacher
    )
    
    return redirect('chat_window', thread_id=thread.id)

@login_required
def chat_window(request, thread_id):
    from django.utils import timezone
    from .models import ChatThread, Message
    from courses.models import Enrollment, Notification
    from django.shortcuts import get_object_or_404, redirect, render
    from django.urls import reverse
    from django.contrib import messages

    # 1. Fetch thread with related data
    thread = get_object_or_404(
        ChatThread.objects.select_related('student', 'teacher', 'course'), 
        id=thread_id
    )
    
    # 2. Security: Only student or teacher of this thread can enter
    if request.user != thread.student and request.user != thread.teacher:
        return redirect('course_list')

    # 3. CHECK ENROLLMENT STATUS
    enrollment = Enrollment.objects.filter(user=thread.student, course=thread.course).first()
    is_finished = enrollment.status == 'finished' if enrollment else False

    # Mark notifications as read
    current_path = reverse('chat_window', args=[thread.id])
    Notification.objects.filter(user=request.user, link=current_path, is_read=False).update(is_read=True)

    # 4. HANDLING SUBMISSION (POST)
    if request.method == 'POST':
        # 🚨 VRO BLOCK: If status is 'finished', NO ONE (Teacher or Student) can send messages.
        if is_finished:
            messages.error(request, "Vro, this chat is locked because the course is finished!")
            return redirect('chat_window', thread_id=thread.id)

        msg_text = request.POST.get('message')
        attachment = request.FILES.get('attachment')

        if msg_text or attachment:
            # Create the message
            Message.objects.create(
                thread=thread, 
                sender=request.user, 
                text=msg_text if msg_text else "", 
                attachment=attachment
            )
            
            # Force update the timestamp so it jumps to the top of the list
            thread.updated_at = timezone.now()
            thread.save() 

            # Notify the recipient
            recipient = thread.teacher if request.user == thread.student else thread.student
            Notification.objects.create(
                user=recipient,
                notification_type='doubt' if request.user == thread.student else 'reply',
                message=f"New message from {request.user.username} in {thread.course.title}",
                link=current_path 
            )
            return redirect('chat_window', thread_id=thread.id)

    # 5. RENDER
    return render(request, 'communications/chat.html', {
        'thread': thread,
        'chat_messages': thread.messages.all().order_by('created_at'),
        'is_finished': is_finished  # This tells the template to hide the input box
    })
@login_required
def edit_message(request, message_id):
    """View to handle editing an existing message - Only sender can edit."""
    # This filter ensures ONLY the sender can find and edit this message
    msg = get_object_or_404(Message, id=message_id, sender=request.user)
    
    # 🔥 VRO BLOCK: Check if course is already finished
    enrollment = Enrollment.objects.filter(user=msg.thread.student, course=msg.thread.course).first()
    if enrollment and enrollment.status == 'finished':
        messages.error(request, "Vro, you can't edit messages after the course is finished!")
        return redirect('chat_window', thread_id=msg.thread.id)

    if request.method == 'POST':
        new_text = request.POST.get('text')
        if new_text:
            msg.text = new_text
            msg.is_edited = True 
            msg.save()
            messages.success(request, "Message updated, vro.")
            
    return redirect('chat_window', thread_id=msg.thread.id)


@login_required
def delete_message(request, message_id):
    """View to handle deleting a message - Only sender can delete."""
    # This filter ensures ONLY the sender can find and delete this specific message
    msg = get_object_or_404(Message, id=message_id, sender=request.user)
    
    # 🔥 VRO BLOCK: Check if course is already finished
    enrollment = Enrollment.objects.filter(user=msg.thread.student, course=msg.thread.course).first()
    if enrollment and enrollment.status == 'finished':
        messages.error(request, "Vro, you can't delete history once the course is finished!")
        return redirect('chat_window', thread_id=msg.thread.id)

    thread_id = msg.thread.id
    msg.delete()
    messages.success(request, "Message deleted.")
    
    return redirect('chat_window', thread_id=thread_id)


@login_required
def course_doubts_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Security: Only the instructor of this course can see this list
    if request.user != course.instructor:
        return redirect('course_list')

    # Get all threads for this course
    threads = ChatThread.objects.filter(course=course).select_related('student').order_by('-updated_at')

    # 🚨 VRO FIX: Get student IDs who have 'finished' status in enrollment
    finished_student_ids = list(Enrollment.objects.filter(
        course=course,
        status='finished'
    ).values_list('user_id', flat=True))

    # Stats logic
    total_queries = threads.count()
    completed_count = threads.filter(student_id__in=finished_student_ids).count()
    active_count = total_queries - completed_count

    return render(request, 'communications/course_doubts.html', {
        'course': course,
        'threads': threads,
        'completed_student_ids': finished_student_ids,
        'active_count': active_count,
        'completed_count': completed_count,
        'total_queries': total_queries
    })