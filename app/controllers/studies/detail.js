import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service(),

    account: null,

    selectedChildId: null,
    selectedChild: Ember.computed('selectedChildId', function () {
        let account = this.get('account');
        if (account) {
            return account.profileById(this.get('selectedChildId'));
        }
    }),

    isAgeEligible: Ember.computed('selectedChild', function () {
        let child = this.get('selectedChild');
        if (!child) {
            return true;
        }
        let experiment = this.get('model');
        return experiment.isEligible(child);
    }),

    route: Ember.computed('model', function () {
        return `${Ember.getOwner(this).lookup('router:main').get('currentPath')}:${this.get('model.id')}`;
    }),
    actions: {
        pickChild() {
            let profile = this.get('selectedChild');
            this.get('session').set('data.profile', profile);
            this.transitionToRoute('participate', this.get('model.id'));
        }
    }
});
