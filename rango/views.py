# Create your views here.
from django.template import RequestContext
from django.shortcuts import render_to_response

from django.http import HttpResponse

from rango.models import Category
from rango.models import Page

from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm
from rango.forms import UserProfileForm

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required


def index(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)

    # find the 5 most likes categories
    category_list = Category.objects.order_by('-likes')[:5]

    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    context_dict = {'categories': category_list}

    # replace space with underscore
    for category in category_list:
        category.url = encode_URL(category.name)


    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    context = RequestContext(request)
    context_dict = {'aboutmessage': "Here is more information"}
    return render_to_response('rango/about.html', context_dict, context)


def category(request, category_name_url):
    context = RequestContext(request)

    # replace spaces with underscores 
    category_name = decode_URL(category_name_url)
    context_dict = {'category_name': category_name,
                    'category_name_url': category_name_url}
    
    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(name=category_name)

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category)
        pages = pages.order_by('-views')[:5]

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass

    return render_to_response('rango/category.html',context_dict,context)


def add_category(request):
    context = RequestContext(request)

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # save the new category to the database
            form.save(commit=True)

            # now call the index() view.
            # the user will be shown the homepage.
            return index(request)
        else:
            # the form had errors
            print form.errors

    else:
        # if it was not a POST, displlay the form
        form = CategoryForm()

    # bad form, no form
    # render the form with error messages
    return render_to_response('rango/add_category.html', {'form': form}, context)





def add_page(request, category_name_url):
    context = RequestContext(request)
    category_name = decode_URL(category_name_url)

    # A HTTP POST?
    if request.method == 'POST':
        form = PageForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # save the new category to the database
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('rango/add_category.html',{}, context)

            page.views = 0
            page.save()

            # return to the category page
            return category(request, category_name_url)
        else:
            # the form had errors
            print form.errors

    else:
        # if it was not a POST, display the form
        form = PageForm()

    # bad form, no form
    # render the form with error messages
    return render_to_response('rango/add_page.html', 
                              {'category_name_url': category_name_url,
                               'category_name': category_name, 'form': form},
                              context)



def register(request):
    context = RequestContext(request)

    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            registered = True

        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    
    return render_to_response('rango/register.html',
                              {'user_form':user_form,
                               'profile_form':profile_form,
                               'registered':registered},
                               context)






def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Your Rango account is disabled")
            
        else:
            #bad login provided
            print "invalid login details: {0}. {1}".format(username,password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        return render_to_response('rango/login.html', {}, context)



@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')


@login_required
def restricted(request):
    return HttpResponse("since you're logged in, you can see this response")


def decode_URL(category_name_url):
    return category_name_url.replace('_',' ')

def encode_URL(category_name):
    return category_name.replace(' ','_')
