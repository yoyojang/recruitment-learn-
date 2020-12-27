from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Q
from interview.models import Candidate


import logging
import csv
from datetime import datetime

from interview import candidate_field as cf

logger = logging.getLogger(__name__)

exportable_fields = ('username', 'city', 'phone', 'bachelor_school', 'master_school', 'degree', 'first_result',
                     'first_interviewer_user', 'second_result', 'second_interviewer_user', 'hr_result', 'hr_score', 'hr_remark', 'hr_interviewer_user')

def export_model_as_csv(modeladmin, request, queryset):
    # 页面动作执行导出csv的功能
    response = HttpResponse(content_type='text/csv')
    field_list = exportable_fields
    response['Content-Disposition'] = 'attachment; filename=recruitment-candidates-list-%s.csv' % (
        datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    )

    # 写入表头
    writer = csv.writer(response)
    writer.writerow(
        [queryset.model._meta.get_field(f).verbose_name.title() for f in field_list]
    )

    for obj in queryset:
        ### 单行的记录（各个字段的值），写到csv文件
        csv_line_value = []
        for field in field_list:
            field_object = queryset.model._meta.get_field(field)
            field_value = field_object.value_from_object(obj)
            # print(field_value)
            csv_line_value.append(field_value)
        writer.writerow(csv_line_value)
    # 用日志记录 操作
    logger.info("%s exported %s candidate records" % (request.user, len(queryset)))

    return response

export_model_as_csv.short_description = u'导出为CSV文件'
export_model_as_csv.allowed_permissions = ('export',)   # 设置用户操作权限（已在model里设置）

# 候选人管理类
class CandidateAdmin(admin.ModelAdmin):
    # 隐藏
    exclude = ('creator','created_date','modified_date')

    actions = (export_model_as_csv,)    #添加页面动作

    # 当前用户是否有导出权限
    def has_export_permission(self, request):
        opts = self.opts
        return request.user.has_perm('%s.%s' % (opts.app_label, 'export'))

    # 显示排列
    list_display = (
        "username","city","bachelor_school","first_score","first_result","first_interviewer_user",
        "second_result","second_interviewer_user","hr_score","hr_result","last_editor"
    )

    # 筛选条件
    list_filter = ('city', 'first_result','second_result','hr_result','first_interviewer_user','second_interviewer_user','second_score')

    # 查询字段
    search_fields = ('username', 'phone', 'email', 'bachelor_school',)

    # 排序
    ordering = ('hr_result', 'second_result','first_result')

    # 一面面试官仅填写一面反馈， 二面面试官可以填写二面反馈
    def get_fieldsets(self, request, obj=None):
        group_names = self.get_group_names(request.user)

        if 'interviewer' in group_names and obj.first_interviewer_user == request.user:
            return cf.default_fieldsets_first
        if 'interviewer' in group_names and obj.second_interviewer_user == request.user:
            return cf.default_fieldsets_second
        return cf.default_fieldsets

    # 对于非管理员，非HR，获取自己是一面面试官或者二面面试官的候选人集合:s
    def get_queryset(self, request):  # show data only owned by the user
        qs = super(CandidateAdmin, self).get_queryset(request)

        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'hr' in group_names:
            return qs
        return Candidate.objects.filter(
            Q(first_interviewer_user=request.user) | Q(second_interviewer_user=request.user))
    # readonly_fields = ('first_interviewer_user', 'second_interviewer_user')  # 设置字段为只读、不可更改

    # list_editable = ('first_interviewer_user', 'second_interviewer_user')   # 直接在列表上修改内容
    default_list_editable = ('first_interviewer_user', 'second_interviewer_user')   # 直接在列表上修改内容

    def get_list_editable(self,request):    # django 没有默认这个函数
        group_names = self.get_group_names(request.user)

        if request.user.is_superuser or 'hr' in group_names:
            return self.default_list_editable
        return ()

    def get_changelist_instance(self, request): # 用上面的函数替换这个函数
        self.list_editable = self.get_list_editable(request)
        return super(CandidateAdmin, self).get_changelist_instance(request)

    def get_group_names(self, user):
        group_names = []
        for g in user.groups.all():
            group_names.append(g.name)
        return group_names

    # 按用户角色来定义字段是否只读
    def get_readonly_fields(self, request, obj=None):
        group_names = self.get_group_names(request.user)

        if 'interviewer' in group_names:
            logger.info("interviewer is in user's group for %s" % request.user.username)
            return ('first_interviewer_user', 'second_interviewer_user',)
        return ()

    fieldsets = (
        (None,{'fields':("userid",( "username", "city", "phone"), ("email", "apply_position", "born_address"), ("gender", "candidate_remark"), ("bachelor_school", "master_school", "doctor_school"), "major", ("test_score_of_general_ability", "paper_score","degree", ), )}),
        ('第一轮面试记录',{'fields':(("first_score"), ("first_learning_ability", "first_professional_competency"), "first_advantage", "first_disadvantage", "first_result", "first_recommend_position", "first_interviewer_user", "first_remark",)}),
        ('第二轮专业复试记录',{'fields':(("second_score"), ("second_learning_ability", "second_professional_competency"), ("second_pursue_of_excellence", "second_communication_ability", "second_pressure_score"), "second_advantage", "second_disadvantage", "second_result", "second_recommend_position", "second_interviewer_user", "second_remark",)}),
        ('HR复试录',{'fields':(("hr_score"), ("hr_responsibility", "hr_communication_ability", "hr_logic_ability"), ("hr_potential", "hr_stability"), "hr_advantage", "hr_disadvantage", "hr_result", "hr_interviewer_user", "hr_remark",)}),
    )

admin.site.register(Candidate, CandidateAdmin)