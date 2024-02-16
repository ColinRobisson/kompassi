import Link from "next/link";
import { notFound } from "next/navigation";

import { graphql } from "@/__generated__";
import { getClient } from "@/apolloClient";
import { auth } from "@/auth";
import DimensionBadge from "@/components/dimensions/DimensionBadge";
import { Field, validateFields } from "@/components/forms/models";
import { SchemaForm } from "@/components/forms/SchemaForm";
import SchemaFormField from "@/components/forms/SchemaFormField";
import SchemaFormInput from "@/components/forms/SchemaFormInput";
import SignInRequired from "@/components/SignInRequired";
import ViewContainer from "@/components/ViewContainer";
import ViewHeading from "@/components/ViewHeading";
import { getTranslations } from "@/translations";

const query = graphql(`
  query ProfileSurveyResponsePage($locale: String!, $responseId: String!) {
    profile {
      forms {
        response(id: $responseId) {
          id
          createdAt
          values

          dimensions {
            ...DimensionBadge
          }

          form {
            slug
            title
            language
            fields
            layout
            event {
              slug
              name
            }
            survey {
              anonymity
            }
          }
        }
      }
    }
  }
`);

interface Props {
  params: {
    locale: string;
    responseId: string;
  };
}

export async function generateMetadata({ params }: Props) {
  const { locale } = params;
  const translations = getTranslations(locale);
  const t = translations.Survey;

  return {
    title: `${t.ownResponsesTitle} – Kompassi`,
  };
}

export const revalidate = 0;

export default async function ProfileSurveyResponsePage({ params }: Props) {
  const { locale, responseId } = params;
  const translations = getTranslations(locale);
  const session = await auth();

  // TODO encap
  if (!session) {
    return <SignInRequired messages={translations.SignInRequired} />;
  }

  const { data } = await getClient().query({
    query,
    variables: {
      responseId,
      locale,
    },
  });

  if (!data.profile?.forms?.response) {
    notFound();
  }

  const t = translations.Survey;

  const response = data.profile.forms.response;
  const { createdAt, form } = response;
  const language = form.language;
  const { fields, layout } = form;
  const values: Record<string, any> = response.values ?? {};

  const anonymity = form.survey?.anonymity;
  const anonymityMessages =
    translations.Survey.attributes.anonymity.secondPerson;

  validateFields(fields);

  // TODO using synthetic form fields for presentation is a hack
  // but it shall suffice until someone comes up with a Design Vision™
  const createdAtField: Field = {
    slug: "createdAt",
    type: "SingleLineText",
    title: t.attributes.createdAt,
  };
  const formattedCreatedAt = createdAt
    ? new Date(createdAt).toLocaleString(locale)
    : "";

  const languageField: Field = {
    slug: "language",
    type: "SingleLineText",
    title: t.attributes.language,
  };

  const dimensions = response.dimensions ?? [];

  function buildDimensionField(dimension: (typeof dimensions)[0]): Field {
    return {
      slug: dimension.dimension.slug,
      type: "SingleLineText",
      title: dimension.dimension.title ?? dimension.dimension.slug,
    };
  }

  return (
    <ViewContainer>
      <Link className="link-subtle" href={`/profile/responses`}>
        &lt; {t.actions.returnToResponseList}
      </Link>

      <div className="d-flex">
        <ViewHeading>
          {t.responseDetailTitle}
          <ViewHeading.Sub>{form.title}</ViewHeading.Sub>
        </ViewHeading>
        {!!dimensions?.length && (
          <h3 className="ms-auto">
            {dimensions.map((dimension) => (
              <DimensionBadge
                key={dimension.dimension.slug}
                dimension={dimension}
              />
            ))}
          </h3>
        )}
      </div>

      {anonymity && (
        <p>
          <small>
            <strong>{anonymityMessages.title}: </strong>
            {anonymityMessages.choices[anonymity]}
          </small>
        </p>
      )}

      <div className="card mb-3">
        <div className="card-body">
          <h5 className="card-title mb-3">{t.attributes.technicalDetails}</h5>

          <SchemaFormField field={createdAtField} layout={layout}>
            <SchemaFormInput
              field={createdAtField}
              value={formattedCreatedAt}
              messages={translations.SchemaForm}
              readOnly
            />
          </SchemaFormField>

          <SchemaFormField field={languageField} layout={layout}>
            <SchemaFormInput
              field={languageField}
              value={language}
              messages={translations.SchemaForm}
              readOnly
            />
          </SchemaFormField>
        </div>
      </div>

      <SchemaForm
        fields={fields}
        values={values}
        layout={layout}
        messages={translations.SchemaForm}
        readOnly
      />
    </ViewContainer>
  );
}
