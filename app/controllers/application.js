import Ember from 'ember';

export default Ember.Controller.extend({
    session: Ember.inject.service(),

    isParticipate: Ember.computed('currentPath', function() {
        return this.get('currentPath') === 'participate';
    }),
    actions: {
        logout() {
            this.get('session').invalidate().then(() => {
                this.transitionToRoute('home');
            });
        }
    }
});
