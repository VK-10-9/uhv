import json
import generate_explanations

# Define manual explanations for the final 22 questions
manual_explanations = {
    "Which value is essential in human-to-human relationship?": [
        "Trust is the foundational value in relationships, representing the assurance that the other person wants my well-being.",
        "Wealth is a physical facility; while it is needed for bodily sustenance, it cannot buy emotional fulfillment or true connection in relationships.",
        "Power creates hierarchy, fear, and division, which are the opposite of the mutual respect and harmony required in relationships.",
        "Fame is temporary external approval and does not establish the inner assurance of mutual happiness that trust provides."
    ],
    "Process of ensuring value-based living is achieved through": [
        "Fear (Bhaya) can force conformity temporarily but leads to resentment and does not foster genuine values.",
        "Greed (Lobha) drives selfish desires and accumulation, causing exploitation rather than value-based harmonious living.",
        "Right understanding (Samyag Darshana) allows us to see relationships and harmony clearly, naturally leading to value-based living.",
        "External enforcement or laws only regulate behavior superficially without changing human consciousness or values."
    ],
    "Result of right utilization of resources?": [
        "Right utilization ensures that resources are used to nurture the body and society, leading to a feeling of prosperity.",
        "Poverty is the lack of physical facilities, which is caused by lack of resources or poor utilization, not right utilization.",
        "Waste is the opposite of right utilization, representing a misuse or neglect of resources.",
        "This option is incorrect because right utilization of resources directly leads to a state of prosperity."
    ],
    "Foundation of humanistic education is based on": [
        "Humanistic education is concerned with human values and consciousness, not merely the accumulation of material wealth.",
        "Right understanding forms the foundation of humanistic education as it enables human beings to live in harmony with themselves and others.",
        "Power leads to domination and control, which contradicts the goal of humanistic education to foster mutual fulfillment.",
        "Fame is an external, temporary desire for recognition and cannot serve as the foundation for holistic educational values."
    ],
    "Role of R&D in context of holistic technologies/systems?": [
        "Profit maximization often leads to resource depletion and exploitation, which is contrary to holistic design.",
        "Holistic systems prioritize collective harmony and ecological balance over isolated individual success.",
        "Competition fosters opposition and conflict, whereas holistic systems require collaboration and mutual fulfillment.",
        "Research and development must aim to create technologies that preserve nature and support human harmony based on right understanding."
    ],
    "What is the process used in value education to verify proposals?": [
        "Self-exploration (Svatantra) is the process of dialoging within oneself to verify proposals on the basis of natural acceptance.",
        "External validation relies on others' opinions, whereas value education encourages finding the truth within ourselves.",
        "Peer review is an academic consensus check and cannot replace the personal realization and validation of values.",
        "Mediation is for resolving external disputes and is not a method for personal value verification."
    ],
    "Continuous happiness and prosperity can be achieved by": [
        "Wealth accumulation only addresses physical needs and does not guarantee happiness in relationships or self-harmony.",
        "While physical health is essential for the body, happiness requires right understanding in the self and harmony in relationships.",
        "Fulfillment at all three levels (self, relationship, and material needs) is the complete formula for continuous happiness and prosperity.",
        "Technology is a tool to produce physical facilities but does not resolve conflicts in relationships or provide inner peace."
    ],
    "Content of value education primarily focuses on": [
        "Economic growth deals only with wealth and does not address the core human need for happiness and relationship harmony.",
        "Physical well-being is necessary for the body, but value education focuses on the values and understanding of the Self.",
        "Materialistic achievements provide temporary pleasure or comfort but do not lead to continuous happiness.",
        "Value education aims to establish right understanding in the self and harmony in human-to-human relationships."
    ],
    "Self-exploration leads to": [
        "Self-exploration helps us realize what is naturally acceptable to us, leading to a clear understanding of human needs.",
        "Wealth is a physical facility; self-exploration guides its right utilization but is not a method to acquire it.",
        "Desires can be chaotic if not guided by right understanding. Self-exploration harmonizes desires rather than blindly pursuing them.",
        "Skills belong to the domain of professional training, whereas self-exploration belongs to the value domain."
    ],
    "What is true about happiness in value education?": [
        "Value education defines happiness as a continuous state of harmony, distinct from temporary sensory pleasures.",
        "Happiness is the state of being in harmony at all levels of existence (self, family, society, nature).",
        "Wealth can lead to prosperity but is not the same as happiness, which is a state of the self.",
        "Problems may exist externally, but happiness is about maintaining inner harmony and right understanding regardless of external challenges."
    ],
    "Method to fulfill basic human aspirations:": [
        "Ignoring norms leads to chaos and opposition, not the fulfillment of aspirations in relationships.",
        "Through self-exploration, we achieve right understanding which is key to satisfying our aspirations for happiness.",
        "Material gains provide physical facilities but cannot satisfy the self's need for continuous happiness and respect.",
        "This option is incorrect because self-exploration and right understanding are indeed the valid methods."
    ],
    "The human being is the co-existence of": [
        "Mind and body is a common dualism, but the mind is only a part of the activities of the Self, not the entire conscious entity.",
        "A human being is a co-existence of the conscious 'Self' (I) and the material 'Body', each having distinct needs and activities.",
        "Heart and mind are both internal aspects of the self and do not represent the co-existence of the conscious and material parts.",
        "While 'soul' is a spiritual term, 'Self' is the precise term used in UHV to describe the conscious entity that has activities of desiring, thinking, and selecting."
    ],
    "Continuous happiness is achieved through": [
        "Wealth only satisfies physical needs and does not guarantee inner peace or relationship harmony.",
        "Power creates opposition and division, which is contrary to harmony and continuous happiness.",
        "Happiness is defined as being in harmony at all levels of living: self, family, society, and nature.",
        "Sensory pleasure is temporary, leading to dependency and excitement, not continuous happiness."
    ],
    "Right understanding in the self leads to": [
        "Wealth is a physical facility and must be produced, whereas right understanding is a state of the self.",
        "Right understanding removes inner contradictions and conflicts, leading directly to a continuous state of happiness.",
        "Right understanding brings clarity and order, eliminating confusion in the self.",
        "Ignorance is the absence of right understanding, which is replaced when understanding is achieved."
    ],
    "Activities of the self are": [
        "Temporary activities belong to the body (like breathing, eating, walking), whereas the self's activities are non-stop.",
        "The activities of the self, such as thinking, desiring, and selecting, are continuous and go on throughout our lives.",
        "Activities of the self do not happen in periodic intervals; we are always desiring or thinking.",
        "Self activities are not random or sporadic; they are a continuous flow of consciousness."
    ],
    "Which is true about happiness/recognition?": [
        "Happiness is not a vague feeling; it is the definite state of harmony that can be systematically understood and realized.",
        "This is a common misconception; happiness is our natural state of acceptance and does not require unhappiness to be recognized.",
        "Harmony brings deep peace and fulfillment, not boredom. Boredom only arises from temporary, repetitive excitements.",
        "Unhappiness causes friction and disharmony; growth in human consciousness occurs through right understanding and harmony."
    ],
    "To be wealthy is ___ condition in the modern world to be happy": [
        "Wealth (material facility) is required for body sustenance, but is not the essential or sufficient condition for continuous happiness of the Self.",
        "If wealth were the essential condition, all rich people would be continuously happy, which is not the case.",
        "This is an ambiguous term and does not accurately describe the relation between wealth and happiness.",
        "This is a misconception of modern consumerist society, which confuses physical facilities with happiness."
    ],
    "Right understanding gained through self-exploration ALSO enables identifying definitiveness of human conduct \u001d called": [
        "Ethical human conduct is the definite behavior of a human living with right understanding and relationship harmony.",
        "Values are the participation of a human being in the larger order, which is a component of, but not the entire conduct itself.",
        "Policy is the framework for protection and enrichment of resources, not the conduct itself.",
        "Utility values refer to the utility of physical objects and facilities, not human conduct."
    ],
    "Self-exploration uses two mechanisms; Natural Acceptance and Experiential validation (alt phrasing check)": [
        "Self-exploration requires verifying a proposal in living (experiential validation) in addition to checking natural acceptance.",
        "Reason alone can be intellectual and theoretical without practical verification in living.",
        "Logical thinking can construct internally consistent arguments that are still false in reality if they are not verified in living.",
        "Theoretical concepts remain as assumptions until they are experientially validated by living accordingly."
    ],
    "Which of the following actions will likely lead to organizational ethical behavior?": [
        "An ethics office provides formal guidelines and assistance, promoting ethical practices.",
        "Promoting moral courage empowers employees to speak up against unethical actions.",
        "Strong governance ensures transparency, accountability, and checks against misconduct.",
        "All three actions are complementary and necessary to build a comprehensive, ethical organizational culture."
    ],
    "___ behavior arises when managers put personal/organizational goals above stakeholder rights": [
        "Putting selfish goals above others' rights is exploitative and cannot be complementary.",
        "Calling it situational is an excuse; violating stakeholders' rights is fundamentally unethical behavior.",
        "Unethical behavior is defined as actions that violate human values, mutual fulfillment, or stakeholder rights.",
        "It is not confusing; it is a clear violation of basic business ethics."
    ],
    "Accepted principles of right or wrong governing conduct of business people are called": [
        "Business is the activity of production, trade, or service, not the ethical framework governing it.",
        "Conduct is behavior in general, whereas the principles of right and wrong are the ethics that govern it.",
        "Business ethics are the specific principles and values that guide ethical decision-making in commercial environments.",
        "Principles is a general term; business ethics is the specific term for conduct governing business people."
    ]
}

def main():
    cache = generate_explanations.load_cache()
    print(f"Initial cache size: {len(cache)}")
    
    # Merge manual explanations
    added = 0
    for q, exps in manual_explanations.items():
        if q not in cache or len(cache[q]) != len(exps):
            cache[q] = exps
            added += 1
            
    generate_explanations.save_cache(cache)
    print(f"Added {added} manual explanations. Current cache size: {len(cache)}")
    
    # Inject into HTML files
    html_content, questions = generate_explanations.parse_html_questions()
    generate_explanations.inject_explanations_to_html(html_content, questions, cache)
    print("Injected explanations into HTML successfully!")

if __name__ == "__main__":
    main()
