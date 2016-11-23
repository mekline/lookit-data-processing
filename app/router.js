import Ember from 'ember';
import config from './config/environment';

const Router = Ember.Router.extend({
  location: config.locationType,
  rootURL: config.rootURL
});

Router.map(function() {
    this.route('home', {path: '/'}, function() {});
    this.route('login', {path: '/login'});
    this.route('studies', function() {
        this.route('detail', {path: '/:experiment_id/'});
        this.route('history');
    });
    this.route('participate', {path: '/participate/:experiment_id/'});

    this.route('faq');
    this.route('scientists');
    this.route('resources');
    this.route('contact');
    this.route('my', {path: '/account'}, function() {
        this.route('demographics');
        this.route('children');
        this.route('email');
    });

    this.route('notfound', {path: '/*path'});
});

export default Router;
