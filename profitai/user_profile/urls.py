from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include
from user_profile import views as user_profile_view
from rest_framework_simplejwt import views as jwt_views
urlpatterns = [
    path('backend/check_phone_numeber/', user_profile_view.CheckPhoneNumberView.as_view(), name="check_phone_number"),
    path('backend/login/', user_profile_view.CustomUserOTPLoginView.as_view(), name='user_login'),
    path('backend/logout/',jwt_views.TokenBlacklistView.as_view()),
    path('backend/tocken/refresh',jwt_views.TokenRefreshView.as_view(),name='token_refresh'),
    path('backend/protected/', user_profile_view.ProtectedAPIView.as_view(), name='protected_api'),
    path('backend/business-profile/', user_profile_view.BusinessProfileListCreateAPIView.as_view(), name='business-profile-list-create'),
    path('backend/business-all/', user_profile_view.BusinessProfileRetrieveUpdateDestroyAPIView.as_view(), name='business-profile-retrieve-update-destroy'),
    path('backend/business/deactivate/', user_profile_view.BusinessProfileDeactivate.as_view(),name="business-deactivate"),
    path('backend/vendor/', user_profile_view.VendorListAPIView.as_view(), name='vendor-list'),
    path('backend/costomer/', user_profile_view.CustomerListCreateAPIView.as_view(), name='costomer-list-create'),
    path('backend/userupdate/',user_profile_view.UserProfileUpdateview.as_view()),
    path("backend/costomer/search",user_profile_view.CustomerSearchAPI.as_view()),
    path("backend/costomer/favourite/add",user_profile_view.CustomerfavouriteAPI.as_view()),
    path("backend/costomer/filter",user_profile_view.CustomerFilterAPIView.as_view()),
    path("backend/costomer/sort",user_profile_view.CustomerSortAPIView.as_view()),
    path("backend/customer/favourite/frequent",user_profile_view.CustomerfavouriteFrequentTopAPI.as_view()),
    path("backend/sales/report",user_profile_view.InvoiceSalesReport.as_view()),
    path("backend/total_amount/report",user_profile_view.AllInvoiceAmountReport.as_view()),
    path("api/zipcode/<str:zipcode>",user_profile_view.get_address_from_zip_code , name="zipcode-api"),
    path("backend/gst-api/",user_profile_view.GSTVerificationAPIView.as_view(),name="gst-api"),
    path('backend/dashboard',user_profile_view.DashboardAPIView.as_view(),name='dashboard-api'),
    path('backend/delete_account',user_profile_view.UserProfitDeleteAPIView.as_view(),name='user-delete-api'),
    path('backend/global_search',user_profile_view.GlobalSearchAPIView.as_view(),name='global-search-api')
]