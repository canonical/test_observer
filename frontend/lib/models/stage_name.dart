import 'family_name.dart';

enum StageName { edge, beta, candidate, stable, proposed, updates }

List<StageName> familyStages(FamilyName family) {
  switch (family) {
    case FamilyName.snap:
      return [
        StageName.edge,
        StageName.beta,
        StageName.candidate,
        StageName.stable,
      ];
    case FamilyName.deb:
      return [
        StageName.proposed,
        StageName.updates,
      ];
    case FamilyName.charm:
      return [
        StageName.edge,
        StageName.beta,
        StageName.candidate,
        StageName.stable,
      ];
  }
}
