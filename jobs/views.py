from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.http import Http404
from django.http import HttpResponseRedirect
from jobs.models import Job, Resume
from jobs.models import Citys,JobTypes

def joblist(request):
    job_list = Job.objects.order_by('job_type')
    # template = loader.get_template('joblist.html')
    context = {'job_list':job_list}

    for job in job_list:
        job.city_name = Citys[job.job_city][1]  # 由于是枚举类型，所以做个转化
        job.job_type = JobTypes[job.job_type][1]

    return render(request, 'joblist.html', context)

def detail(request, job_id):
    try:
        job = Job.objects.get(pk=job_id)
        job.city_name = Citys[job.job_city][1]
    except Job.DoesNotExist:
        raise Http404("Job does not exist.")

    return render(request, 'job.html', {'job': job})


class ResumeCreateView(LoginRequiredMixin, CreateView):
    """    简历职位页面  """
    template_name = 'resume_form.html'
    success_url = '/joblist/'
    model = Resume
    fields = ["username", "city", "phone",
        "email", "apply_position", "gender",
        "bachelor_school", "master_school", "major", "degree", "picture", "attachment",
        "candidate_introduction", "work_experience", "project_experience"]

    ### 从 URL 请求参数带入默认值
    def get_initial(self):
        initial = {}
        for x in self.request.GET:
            initial[x] = self.request.GET[x]
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.applicant = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())
