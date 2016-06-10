import Ember from 'ember';

import AuthenticatedRouteMixin from 'ember-simple-auth/mixins/authenticated-route-mixin';


export default Ember.Route.extend(AuthenticatedRouteMixin, {

    model( /*params*/ ) {
        let Experiment = this.store.modelFor('experiment');

        // Return the result of a query for all experiments
        return this.store.query('experiment', {
            q: `state:${Experiment.prototype.ACTIVE} OR state:${Experiment.prototype.ARCHIVED}`
        }).then((experiments) => {
            let promises = [];
            let experimentSessions = [];

            experiments.forEach((experiment) => {
                promises.push( // Endpoint only returns sessions that the user has permissions to see (assumption: only their own)
                    this.store.query(experiment.get('sessionCollectionId'), {
                        'filter[completed]': 1
                    }).then((sessions) => {
                        if (sessions.get('length') > 0) {
                            experimentSessions.push({
                                experiment: experiment,
                                sessions: sessions
                            });
                        }
                    }));
            });

            return Ember.RSVP.all(promises).then(() => {
                return experimentSessions;
            });
        });
    }
});
