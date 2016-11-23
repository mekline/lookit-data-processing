import Ember from 'ember';

export default {
    min (lower) {
        return (value) => {
            return value >= lower;
        };
    },
    max (upper) {
        return (value) => {
            return value <= upper;
        };
    },
    join (...validators) {
        return (value) => {
            Ember.computed.and(
                validators.map((validator) => {
                    return validator(value);
                })
            );
        };
    }
};
