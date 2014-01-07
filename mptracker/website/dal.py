from datetime import date
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from jinja2 import filters
from mptracker.models import (
    County,
    Person,
    Mandate,
    MpGroup,
    MpGroupMembership,
    Proposal,
    ProposalActivityItem,
    Sponsorship,
    Transcript,
    Question,
    Ask,
    Match,
    VotingSession,
    Vote,
    GroupVote,
    PolicyDomain,
    NameSearch,
)


def _get_recent_questions(mandate, limit):
    recent_questions_query = (
        Question.query
        .order_by(Question.date.desc())
    )

    if mandate is not None:
        recent_questions_query = (
            recent_questions_query
            .join(Question.asked)
            .filter(Ask.mandate == mandate)
        )

    return [
        {
            'date': q.date,
            'text': filters.do_truncate(q.title),
            'type': q.type,
            'question_id': q.id,
        }
        for q in recent_questions_query.limit(limit)
    ]


def _get_recent_proposals(mandate, limit):
    recent_proposals_query = (
        Proposal.query
        .order_by(Proposal.date.desc())
    )

    if mandate is not None:
        recent_proposals_query = (
            recent_proposals_query
            .join(Proposal.sponsorships)
            .filter(Sponsorship.mandate == mandate)
        )

    return [
        {
            'date': p.date,
            'text': p.title,
            'type': 'proposal',
            'proposal_id': p.id,
        }
        for p in recent_proposals_query.limit(limit)
    ]


def _get_recent_activity(mandate):
    recent_transcripts_query = (
        mandate.transcripts
        .order_by(Transcript.serial.desc())
        .limit(5)
        .options(joinedload('chapter'))
    )
    recent_transcripts = [
        {
            'date': t.chapter.date,
            'text': filters.do_truncate(t.text, 200),
            'type': 'speech',
        }
        for t in recent_transcripts_query
    ]

    recent_questions = _get_recent_questions(mandate, 5)
    recent_proposals = _get_recent_proposals(mandate, 5)

    rv = recent_transcripts + recent_questions + recent_proposals
    rv.sort(key=lambda r: r['date'], reverse=True)
    return rv[:10]


class DalPerson:

    def __init__(self, person_id, missing=KeyError):
        self.person = Person.query.get(person_id)
        if self.person is None:
            raise missing()

        self.mandate = (
            Mandate.query
            .filter_by(person=self.person)
            .filter_by(year=2012)
            .first()
        )
        if self.mandate is None:
            raise missing()

    def get_main_details(self):
        return {
            'name': self.person.name,
        }

    @property
    def _local_ask_query(self):
        return (
            self.mandate.asked
            .join(Ask.match_row)
            .filter(Match.score > 0)
        )

    @property
    def _local_sponsorship_query(self):
        return (
            self.mandate.sponsorships
            .join(Sponsorship.match_row)
            .filter(Match.score > 0)
        )

    def get_details(self):
        rv = self.get_main_details()
        rv.update({
            'romania_curata_text': self.person.romania_curata,
            'position_list': [
                {
                    'title': p.title,
                    'start_date': p.interval.lower,
                    'end_date': p.interval.upper,
                }
                for p in self.person.positions
            ],
        })

        membership_query = (
            self.mandate.group_memberships
            .order_by(MpGroupMembership.interval.desc())
        )
        group_history = [
            {
                'start_date': membership.interval.lower,
                'end_date': membership.interval.upper,
                'role': membership.role,
                'group_short_name': membership.mp_group.short_name,
                'group_id': membership.mp_group_id,
            }
            for membership in membership_query
        ]

        rv['group_history'] = group_history

        if self.mandate.county:
            rv['college'] = {
                'county_name': self.mandate.county.name,
                'number': self.mandate.college,
            }

        voting_session_count = (
            VotingSession.query
            .filter(VotingSession.final == True)
            .count()
        )
        final_votes = (
            self.mandate.votes
            .join(Vote.voting_session)
            .filter(VotingSession.final == True)
        )
        votes_attended = final_votes.count()
        votes_loyal = final_votes.filter(Vote.loyal == True).count()

        rv['vote'] = {
            'attendance': votes_attended / voting_session_count,
        }
        if votes_attended > 0:
            rv['vote']['loyalty'] = votes_loyal / votes_attended

            votes_with_cabinet = (
                final_votes
                .filter(Vote.loyal_to_cabinet != None)
                .count()
            )
            if votes_with_cabinet:
                votes_cabinet_loyal = (
                    final_votes
                    .filter(Vote.loyal_to_cabinet == True)
                    .count()
                )
                rv['vote']['cabinet_loyalty'] = (
                    votes_cabinet_loyal / votes_with_cabinet
                )

        rv['speeches'] = self.mandate.transcripts.count()
        rv['proposals'] = self.mandate.sponsorships.count()
        rv['local_score'] = (
            self._local_ask_query.count() +
            self._local_sponsorship_query.count()
        )

        rv['recent_activity'] = _get_recent_activity(self.mandate)

        if self.mandate.picture_url is not None:
            rv['picture_filename'] = '%s-300px.jpg' % str(self.mandate.id)

        return rv

    def get_local_activity(self):
        return {
            'proposal_list': [
                {
                    'id': sp.proposal.id,
                    'date': sp.proposal.date,
                    'title': sp.proposal.title,
                }
                for sp in (
                    self._local_sponsorship_query
                    .options(joinedload('proposal'))
                    .join(Sponsorship.proposal)
                    .order_by(Proposal.date.desc())
                )
            ],

            'question_list': [
                {
                    'id': ask.question.id,
                    'date': ask.question.date,
                    'title': ask.question.title,
                }
                for ask in (
                    self._local_ask_query
                    .options(joinedload('question'))
                    .join(Ask.question)
                    .order_by(Question.date.desc())
                )
            ],
        }


class DataAccess:

    def get_county_name_map(self):
        return {c.code: c.name for c in County.query}

    def get_2012_mandates_by_county(self):
        mandates = (
            Mandate.query
            .filter_by(year=2012)
            .join(Mandate.person)
            .join(Mandate.county)
        )

        mandate_data = defaultdict(list)
        for m in mandates:
            key = '%s%d' % (m.county.code, m.college)
            mandate_data[key].append({
                'name': m.person.name,
                'person_id': m.person_id,
            })

        return dict(mandate_data)

    def search_person(self, query):
        name_search = NameSearch(
            Person.query
            .join(Person.mandates)
            .filter_by(year=2012)
            .order_by(Person.name)
        )
        return [
            {'name': person.name, 'id': person.id}
            for person in name_search.find(query.strip())
        ]

    def get_person(self, person_id, missing=KeyError):
        return DalPerson(person_id, missing)

    def get_recent_proposals(self):
        return _get_recent_proposals(None, 10)

    def get_recent_questions(self):
        return _get_recent_questions(None, 10)

    def get_question_details(self, question_id, missing=KeyError):
        question = Question.query.get(question_id)
        if question is None:
            raise missing()

        rv = {'title': question.title, 'text': question.text}

        asked_query = (
            Person.query
            .join(Person.mandates)
            .join(Mandate.asked)
            .filter(Ask.question == question)
        )
        rv['asked_by'] = []
        for person in asked_query:
            rv['asked_by'].append({
                'name': person.name,
                'id': person.id,
            })

        return rv

    def get_party_list(self):
        return [
            {'name': group.name, 'id': group.id}
            for group in MpGroup.query.order_by(MpGroup.name)
            if group.short_name not in ['Indep.', 'Mino.']
        ]

    def get_party_details(self, party_id, missing=KeyError):
        party = MpGroup.query.get(party_id)
        if party is None:
            raise missing()
        rv = {'name': party.name}

        rv['member_list'] = []
        memberships_query = (
            party.memberships
            .filter(
                MpGroupMembership.interval.contains(date.today())
            )
            .options(
                joinedload('mandate'),
                joinedload('mandate.person'),
            )
            .join(MpGroupMembership.mandate)
            .join(Mandate.person)
            .order_by(Person.name)
        )
        for membership in memberships_query:
            person = membership.mandate.person
            rv['member_list'].append({
                'name': person.name,
                'id': person.id,
            })

        final_votes = (
            Vote.query
            .join(Vote.voting_session)
            .filter(VotingSession.final == True)
            .join(Vote.mandate)
            .join(Mandate.group_memberships)
            .filter(MpGroupMembership.mp_group_id == party_id)
        )
        votes_attended = final_votes.count()
        votes_loyal = final_votes.filter(Vote.loyal == True).count()
        rv['member_loyalty'] = votes_loyal / votes_attended

        group_votes = GroupVote.query.filter(GroupVote.mp_group == party)
        loyal_group_votes = group_votes.filter_by(loyal_to_cabinet=True)
        rv['cabinet_loyalty'] = loyal_group_votes.count() / group_votes.count()

        return rv

    def get_policy_list(self):
        return [
            {'name': policy.name, 'id': policy.id}
            for policy in PolicyDomain.query
        ]

    def get_policy(self, policy_id, missing=KeyError):
        policy = PolicyDomain.query.get(policy_id)
        if policy is None:
            raise missing()
        return {'name': policy.name}

    def get_policy_proposal_list(self, policy_id):
        proposal_query = (
            Proposal.query
            .filter_by(policy_domain_id=policy_id)
        )
        return [
            {
                'title': proposal.title,
                'id': proposal.id,
                'status': proposal.status,
            }
            for proposal in proposal_query
        ]

    def get_proposal_details(self, proposal_id, missing=KeyError):
        proposal = Proposal.query.get(proposal_id)
        if proposal is None:
            raise missing()
        rv = {'title': proposal.title}

        rv['activity'] = []
        activity_query = (
            proposal.activity
            .order_by(ProposalActivityItem.order.desc())
        )
        for item in activity_query:
            rv['activity'].append({
                'date': item.date,
                'location': item.location.lower(),
                'html': item.html,
            })

        sponsors_query = (
            Person.query
            .join(Person.mandates)
            .join(Mandate.sponsorships)
            .filter(Sponsorship.proposal == proposal)
        )
        rv['sponsors'] = []
        for person in sponsors_query:
            rv['sponsors'].append({
                'name': person.name,
                'id': person.id,
            })

        return rv
